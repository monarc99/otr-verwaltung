# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from gtk import events_pending, main_iteration, RESPONSE_OK
import base64
import subprocess
import urllib
import os
from os.path import basename, join, dirname, exists, splitext
import time
import re

from otrverwaltung import fileoperations
from otrverwaltung.conclusions import FileConclusion
from otrverwaltung.constants import Action, Cut_action, Status, Format, Program
from otrverwaltung.actions.baseaction import BaseAction
from otrverwaltung import codec
from otrverwaltung import cutlists as cutlists_management
from otrverwaltung import path
from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung.gui import CutinterfaceDialog
from fractions import Fraction

class DecodeOrCut(BaseAction):
    
    def __init__(self, app, gui):
        self.update_list = True
        self.__app = app
        self.config = app.config
        self.__gui = gui

    def do(self, action, filenames, cut_action=None):
        self.rename_by_schema = self.__app.rename_by_schema
        
        decode, cut = False, False            
            
        # prepare tasks
        if action == Action.DECODE:
            self.__gui.main_window.set_tasks_text('Dekodieren')
            decode = True
        elif action == Action.CUT:
            self.__gui.main_window.set_tasks_text('Schneiden')
            cut = True
        else: # decode and cut
            self.__gui.main_window.set_tasks_text('Dekodieren/Schneiden')        
            decode, cut = True, True
                                       
        file_conclusions = []
            
        if decode:
            for otrkey in filenames:
                file_conclusions.append(FileConclusion(action, otrkey=otrkey))
            
        if cut and not decode: # dont add twice
            for uncut_video in filenames:
                file_conclusions.append(FileConclusion(action, uncut_video=uncut_video))
                        
        # decode files                    
        if decode:
            if self.decode(file_conclusions) == False: 
                return
            
        # cut files
        if cut:
            if self.cut(file_conclusions, action, cut_action) == False: 
                return

        self.__gui.main_window.block_gui(False)

        # no more need for tasks view
        self.__gui.main_window.set_tasks_visible(False)

        show_conclusions = False
        # Only cut - don't show conclusions if all were cancelled
        if action == Action.CUT:
            for conclusion in file_conclusions:
                if conclusion.cut.status != Status.NOT_DONE:
                    show_conclusions = True
                    break
                    
        # Only decode - don't show if everything is OK
        elif action == Action.DECODE:
            for conclusion in file_conclusions:
                if conclusion.decode.status != Status.OK:
                    show_conclusions = True
                    
            if not show_conclusions:
                self.__app.gui.main_window.change_status(0, "%i Datei(en) erfolgreich dekodiert" % len(file_conclusions), permanent=True)
        
        # Decode and cut - always show      
        else: 
            show_conclusions = True
                                
        if show_conclusions:                
            self.__app.conclusions_manager.add_conclusions(*file_conclusions)

    def decode(self, file_conclusions):          
            
        # no decoder        
        if not "decode" in self.config.get('general', 'decoder'): # no decoder specified
            # dialog box: no decoder
            self.__gui.message_error_box("Es ist kein korrekter Dekoder angegeben!")
            return False
        
        # retrieve email and password
        email = self.config.get('general', 'email')
        password = base64.b64decode(self.config.get('general', 'password')) 

        if not email or not password:
            self.__gui.dialog_email_password.set_email_password(email, password)       
        
            # let the user type in his data through a dialog
            response = self.__gui.dialog_email_password.run()
            self.__gui.dialog_email_password.hide()
            
            if response == RESPONSE_OK:
                email, password = self.__gui.dialog_email_password.get_email_password()                  
            else: # user pressed cancel
                return False                        
        
        # now this method may not return "False"
        self.__gui.main_window.set_tasks_visible(True)
        self.__gui.main_window.block_gui(True)
                   
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
            # update progress
            self.__gui.main_window.set_tasks_text("Datei %s/%s dekodieren" % (count + 1, len(file_conclusions)))
                   
            verify = True                   

            command = [self.config.get('general', 'decoder'), "-i", file_conclusion.otrkey, "-e", email, "-p", password, "-o", self.config.get('general', 'folder_uncut_avis')]
                      
            if not self.config.get('general', 'verify_decoded'):
                verify = False
                command += ["-q"]              

            try:       
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            except OSError:
                file_conclusion.decode.status = Status.ERROR
                file_conclusion.decode.message = "Dekoder wurde nicht gefunden."
                continue               
 
            while True:
                l = ""
                while True:
                    c = process.stdout.read(1)
                    if c == "\r" or c == "\n":
                        break
                    l += c
        
                if not l:
                    break
        
                try:                             
                    if verify:   
                        file_count = count + 1, len(file_conclusions)
                                                        
                        if "input" in l:
                            self.__gui.main_window.set_tasks_text("Eingabedatei %s/%s kontrollieren" % file_count)
                        elif "output" in l:
                            self.__gui.main_window.set_tasks_text("Ausgabedatei %s/%s kontrollieren" % file_count)
                        elif "Decoding" in l:
                            self.__gui.main_window.set_tasks_text("Datei %s/%s dekodieren" % file_count)
                                                        
                    progress = int(l[10:13])                    
                    # update progress
                    self.__gui.main_window.set_tasks_progress(progress)
                    
                    while events_pending():
                        main_iteration(False)
                except ValueError:                
                    pass
           
            # errors?            
            errors = process.stderr.readlines()
            error_message = ""
            for error in errors:
                error_message += error.strip()
                                                  
            if len(errors) == 0: # dekodieren erfolgreich                
                file_conclusion.decode.status = Status.OK
                
                file_conclusion.uncut_video = join(self.config.get('general', 'folder_uncut_avis'), basename(file_conclusion.otrkey[0:len(file_conclusion.otrkey)-7]))
                             
                # move otrkey to trash
                target = self.config.get('general', 'folder_trash_otrkeys')
                fileoperations.move_file(file_conclusion.otrkey, target)
            else:            
                file_conclusion.decode.status = Status.ERROR

                try:
                    unicode(error_message)
                except UnicodeDecodeError:
                    error_message = unicode(error_message, 'iso-8859-1')

                file_conclusion.decode.message = error_message
                
        return True
            
    def cut(self, file_conclusions, action, default_cut_action=None):                      
        # now this method may not return "False"
        self.__gui.main_window.set_tasks_visible(True)
        self.__gui.main_window.block_gui(True)          
             
        if not default_cut_action:
            default_cut_action = self.config.get('general', 'cut_action')                                         
               
        for count, file_conclusion in enumerate(file_conclusions):
            self.__gui.main_window.set_tasks_text("Cutlist %s/%s wählen" % (count + 1, len(file_conclusions)))
            self.__gui.main_window.set_tasks_progress((count + 1) / float(len(file_conclusions)) * 100)
    
            # file correctly decoded?            
            if action == Action.DECODEANDCUT:
                if file_conclusion.decode.status != Status.OK:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Datei wurde nicht dekodiert."
                    continue
           
            file_conclusion.cut.cut_action = default_cut_action
                                         
            if default_cut_action in [Cut_action.ASK, Cut_action.CHOOSE_CUTLIST]:
                # show dialog                
                self.__gui.dialog_cut.setup(
                    file_conclusion.uncut_video,
                    self.config.get('general', 'folder_cut_avis'),
                    default_cut_action == Cut_action.ASK)                    
                    
                cutlists = []                              
                self.cutlists_error = False
                
                def error_cb(error):            
                    self.__gui.dialog_cut.builder.get_object('label_status').set_markup("<b>%s</b>" % error)
                    self.cutlists_error = True
                     
                def cutlist_found_cb(cutlist):
                    self.__gui.dialog_cut.add_cutlist(cutlist)
                    cutlists.append(cutlist)
               
                def completed():
                    if not self.cutlists_error:
                        self.__gui.dialog_cut.builder.get_object('label_status').set_markup("")
               
                GeneratorTask(cutlists_management.download_cutlists, None, completed).start(file_conclusion.uncut_video, self.config.get('general', 'server'), self.config.get('general', 'choose_cutlists_by'), self.config.get('general', 'cutlist_mp4_as_hq'), error_cb, cutlist_found_cb)
                
                response = self.__gui.dialog_cut.run()                
                self.__gui.dialog_cut.hide()

                if response < 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen."                    
                else:  # change cut_action accordingly
                    file_conclusion.cut.cut_action = response

            if file_conclusion.cut.cut_action == Cut_action.MANUALLY: # MANUALLY                               
                error_message, cutlist = self.cut_file_manually(file_conclusion.uncut_video)
                                       
                if not error_message:
                    file_conclusion.cut.create_cutlist = True
                    file_conclusion.cut.upload_cutlist = True
                    file_conclusion.cut.cutlist = cutlist
                else:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error_message
                    
            elif file_conclusion.cut.cut_action == Cut_action.BEST_CUTLIST:
                error, cutlists = cutlists_management.download_cutlists(file_conclusion.uncut_video, self.config.get('general', 'server'), self.config.get('general', 'choose_cutlists_by'), self.config.get('general', 'cutlist_mp4_as_hq'))
                
                if error:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error
                    continue
                
                if len(cutlists) == 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Keine Cutlist gefunden."
                    continue
                                               
                file_conclusion.cut.cutlist = cutlists_management.get_best_cutlist(cutlists)
             
            elif file_conclusion.cut.cut_action == Cut_action.CHOOSE_CUTLIST:                
                file_conclusion.cut.cutlist = self.__gui.dialog_cut.chosen_cutlist
                
            elif file_conclusion.cut.cut_action == Cut_action.LOCAL_CUTLIST:     
                file_conclusion.cut.cutlist.local_filename = file_conclusion.uncut_video + ".cutlist"
                
                if not exists(file_conclusion.cut.cutlist.local_filename):
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = "Keine lokale Cutlist gefunden."          
          
        # and finally cut the file
        # waitsound = subprocess.Popen([self.config.get('general', 'mplayer'), "-vo", "null", "-loop", "0", path.get_image_path('waitsound.mp3')])
        for count, file_conclusion in enumerate(file_conclusions):            
            
            if file_conclusion.cut.status in [Status.NOT_DONE, Status.ERROR]:
                continue    
        
            print "[Decodeandcut] Datei %s wird geschnitten" % file_conclusion.uncut_video
            self.__gui.main_window.set_tasks_text("Datei %s/%s schneiden" % (count + 1, len(file_conclusions)))
            self.__gui.main_window.set_tasks_progress(0.5)
            
            # download cutlist
            if file_conclusion.cut.cut_action in [Cut_action.BEST_CUTLIST, Cut_action.CHOOSE_CUTLIST]:
                file_conclusion.cut.cutlist.download(self.config.get('general', 'server'), file_conclusion.uncut_video)   

            cut_video, ac3_file, error = self.cut_file_by_cutlist(file_conclusion.uncut_video, file_conclusion.cut.cutlist)                

            if cut_video == None:
                file_conclusion.cut.status = Status.ERROR
                file_conclusion.cut.message = error    
            else:
                file_conclusion.cut.status = Status.OK
                file_conclusion.cut_video = cut_video
                file_conclusion.ac3_file = ac3_file
                
                if self.config.get('general', 'rename_cut'):                        
                    file_conclusion.cut.rename = self.rename_by_schema(basename(file_conclusion.cut_video)) # rename after cut video, extension could have changed
                else:
                    file_conclusion.cut.rename = basename(cut_video)
        # waitsound.kill()
        return True

    def __get_format(self, filename):        
        root, extension = splitext(filename)
        
        if extension == '.avi':
            if splitext(root)[1] == '.HQ':
                format = Format.HQ
                ac3name = splitext(root)[0] + ".HD.ac3"
            elif splitext(root)[1] == '.HD':
                format = Format.HD
                ac3name = root + ".ac3"
            else:
                format = Format.AVI
                ac3name = root + ".HD.ac3"
        elif extension == '.mp4':
            format = Format.MP4
            ac3name = root + ".HD.ac3"
        else:
            return -1, None
            
        if os.path.isfile(ac3name):
	    return format, ac3name
	else:
	    return format, None

    def __get_program(self, filename, manually=False):   
        if manually:
            programs = { Format.AVI : self.config.get('general', 'cut_avis_man_by'),
                         Format.HQ  : self.config.get('general', 'cut_hqs_man_by'),
                         Format.HD  : self.config.get('general', 'cut_hqs_man_by'),
                         Format.MP4 : self.config.get('general', 'cut_mp4s_man_by') }
        else:
            programs = { Format.AVI : self.config.get('general', 'cut_avis_by'),
                         Format.HQ  : self.config.get('general', 'cut_hqs_by'),
                         Format.HD  : self.config.get('general', 'cut_hqs_by'),                         
                         Format.MP4 : self.config.get('general', 'cut_mp4s_by') }
                     
        format, ac3 = self.__get_format(filename)                 
        if not self.config.get('general', 'merge_ac3s'):
        	ac3 = None

        if format < 0:
            return -1, "Format konnte nicht bestimmt werden/wird noch nicht unterstützt.", False
                             
        config_value = programs[format]
        
        if 'avidemux' in config_value:
            return Program.AVIDEMUX, config_value, ac3
        elif 'intern-VirtualDub' in config_value:
	    return Program.VIRTUALDUB, path.get_image_path('intern-VirtualDub') + '/VirtualDub.exe', ac3 
        elif 'intern-vdub' in config_value:
	    return Program.VIRTUALDUB, path.get_image_path('intern-VirtualDub') + '/vdub.exe', ac3 
        elif 'vdub' in config_value or 'VirtualDub' in config_value:
            return Program.VIRTUALDUB, config_value, ac3
        elif 'CutInterface' in config_value and manually:
            return Program.CUT_INTERFACE, config_value, ac3
        else:
            return -2, "Programm '%s' konnte nicht bestimmt werden. Es werden VirtualDub und Avidemux unterstützt." % config_value, False 
   
    def __generate_filename(self, filename, forceavi=0):
        """ generate filename for a cut video file. """
        
        root, extension = splitext(basename(filename))
        if forceavi == 1:
            extension = '.avi'
        new_name = root + "-cut" + extension
                
        cut_video = join(self.config.get('general', 'folder_cut_avis'), new_name)        
            
        return cut_video
   
    def __get_fps(self, filename):
        """ Gets the fps of a movie using mplayer. 
            Returns without error:              
                       fps, None
                    with error:
                       None, error_message """
        
        mplayer = self.config.get('general', 'mplayer')
            
        if not mplayer:
            return None, "Der Mplayer ist nicht angegeben. Dieser wird zur Bestimmung der FPS benötigt."

        try:
            process = subprocess.Popen([mplayer, "-vo", "null", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE)       
        except OSError:
            return None, "MPlayer wurde nicht gefunden!"            
        
        stdout = process.communicate()[0]
    
        for line in stdout.split('\n'):
            if "VIDEO" in line:
                try:
                    return float(line[line.index("bpp")+3 : line.index("fps")]), None
                except:
                    return None, "FPS konnte nicht bestimmt werden " + line
      
        return None, "FPS konnte nicht bestimmt werden."
        
    
    def __get_aspect_ratio(self, filename):
        """ Gets the aspect ratio of a movie using mplayer. 
            Returns without error:              
                       aspect_ratio, None
                    with error:
                       None, error_message """
        mplayer = self.config.get('general', 'mplayer')
            
        if not mplayer:
            return None, "Der Mplayer ist nicht angegeben. Dieser wird zur Bestimmung der Aspekt Ratio benötigt."

        try:
            process = subprocess.Popen([mplayer, "-vo", "null", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE)       
        except OSError:
            return None, "MPlayer wurde nicht gefunden!"            
        
        stdout = process.communicate()[0]
    
        for line in stdout.split('\n'):
            if "Aspe" in line:
                if "1.78:1" in line or "0.56:1" in line:
                    return "16:9", None
                elif "1.33:1" in line or "0.75:1" in line:
                    return "4:3", None
                else:
                    return None, "Aspekt konnte nicht bestimmt werden " + line
      
        return None, "Aspekt Ratio konnte nicht bestimmt werden."            

    def __get_sample_aspect_ratio(self, filename):
        """ Gets the aspect ratio of a movie using mplayer. 
            Returns without error:              
                       aspect_ratio, None
                    with error:
                       None, error_message """
        mplayer = self.config.get('general', 'mplayer')
            
        if not mplayer:
            return None, "Der Mplayer ist nicht angegeben. Dieser wird zur Bestimmung der Sample Aspekt Ratio benötigt."

        try:
            process = subprocess.Popen([mplayer, "-msglevel", "all=6", "-vo", "null", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE)       
        except OSError:
            return None, "MPlayer wurde nicht gefunden!"            
        
        stdout = process.communicate()[0]

        infos_match = re.compile(r"VO Config \((\d{1,})x(\d{1,})->(\d{1,})x(\d{1,})")    

        for line in stdout.split('\n'):
            m = re.search(infos_match,line)
            
	    if m:
                sar = Fraction(  int(m.group(3)),  int(m.group(1))  )
                if sar.numerator == 427 and sar.denominator == 360:
                    return "32:27", None
                else:
                    return str(sar.numerator) + ":" + str(sar.denominator), None
            else:
                pass
   
        return None, "Sample Aspekt Ratio konnte nicht bestimmt werden."            
          
    def __create_cutlist_virtualdub(self, filename):
        """ returns: cuts, error_message """
        
        try:
            f = open(filename, 'r')
        except IOError:
            return None, "Die VirtualDub-Projektdatei konnte nicht gelesen werden.\nWurde das Projekt in VirtualDub nicht gespeichert?\n(Datei: %s)." % filename

        cuts_frames = [] # (start, duration)
        count = 0

        for line in f.readlines():
            if "VirtualDub.subset.AddRange" in line:
                try:
                    start, duration = line[line.index('(') + 1 : line.index(')')].split(',')
                except (IndexError, ValueError), message:
                    return None, "Konnte Schnitte nicht lesen, um Cutlist zu erstellen. (%s)" % message
                
                cuts_frames.append((int(start), int(duration)))
                
        if len(cuts_frames) == 0:
            return None, "Konnte keine Schnitte finden!"

        fileoperations.remove_file(filename)

        return cuts_frames, None       
       
    def cut_file_manually(self, filename):
        """ Cuts a file manually with Avidemux or VirtualDub or the CutInterface and gets cuts from
            possibly created project files (VD) or from output (AD). 
            returns: error_message, cutlist """
        
        program, config_value, ac3file = self.__get_program(filename, manually=True)
        
        if program < 0:
            return config_value, None
            
        cutlist = cutlists_management.Cutlist()
        if program == Program.AVIDEMUX:       

            try:                   
                avidemux = subprocess.Popen([config_value, filename], stdout=subprocess.PIPE)
            except OSError:
                return "Avidemux konnte nicht aufgerufen werden: " + config_value, None
                
            while avidemux.poll() == None:
                time.sleep(1)
                pass
                
            seg_lines = []
            
            for line in avidemux.stdout.readlines():       
                if line.startswith(' Seg'):
                    # delete not interesting parts
                    line = line[:line.find("audio")]
                
                    parts = line.split(',')
        
                    seg_id = int(parts[0].split(':')[-1])
                    start = int(parts[1].split(':')[-1])
                    size = int(parts[2].split(':')[-1])
                    seg_lines.append((seg_id, start, size))
 
            # keep only necessary items            
            seg_lines.reverse()
            temp_cuts = []
            
            for seg_id, start, duration in seg_lines:
                if seg_id == 0:
                    temp_cuts.append((start, duration))
                    break
                else:
                    temp_cuts.append((start, duration))
                
            temp_cuts.reverse()
            
            cuts_frames = []
            count = 0
            for start, duration in temp_cuts:
                cuts_frames.append((start, duration))
                count += 1                         
                
            if len(cuts_frames) == 0:
                cutlist_error = "Es wurde nicht geschnitten."
            else:
                cutlist_error = None
                        
        elif program == Program.VIRTUALDUB: # VIRTUALDUB
            
            cut_video_is_none, error = self.__cut_file_virtualdub(filename, config_value, cuts=None, manually=True)
            
            if error != None:
                return error, None
                
            cuts_frames, cutlist_error = self.__create_cutlist_virtualdub(join(self.config.get('general', 'folder_uncut_avis'), "cutlist.vcf"))
        
        if program == Program.CUT_INTERFACE:
            # looking for latest cutlist, if any
            p, video_file = os.path.split(filename)
            cutregex = re.compile("^" + video_file + "\.?(.*).cutlist$")
            files = os.listdir(p)
            number = -1
            local_cutlist = None		# use fallback name in conclusions if there are no local cutlists
            for f in files:
                match = cutregex.match(f)
                if match:
                    # print "Found local cutlist %s" % match.group()
                    if match.group(1) == '':
                        res_num = 0
                    else:
                        res_num = int(match.group(1))
                    
                    if res_num > number:
                        res_num = number
                        local_cutlist = p + "/" + match.group()
                    
            ci = CutinterfaceDialog.NewCutinterfaceDialog()
            cutlist = ci._run(filename , local_cutlist, self.__app)
            ci.destroy()
            
            if cutlist.cuts_frames == None or len(cutlist.cuts_frames) == 0:
                cutlist_error = "Keine Schnitte angegeben"
            else:
                cutlist_error = None
            
        else:
            # create cutlist data
            if cutlist_error == None:
                cutlist.cuts_frames = cuts_frames
                cutlist.intended_app = basename(config_value)                    
                cutlist.usercomment = 'Mit OTR-Verwaltung geschnitten'
                
                fps, error = self.__get_fps(filename)
                if not error:
                    cutlist.fps = fps
                else:
                    cutlist.fps = 25.
                    print "Achtung! Möglicherweise wurde eine falsche Fps-Anzahl eingetragen! (%s)" % error
                # calculate seconds
                for start_frame, duration_frames in cuts_frames:
                    cutlist.cuts_seconds.append((start_frame / fps, duration_frames / fps))
        
        if cutlist_error:            
            return cutlist_error, None
        else:
            return None, cutlist
             
    def cut_file_by_cutlist(self, filename, cutlist):
        """ Returns: cut_video, ac3file, error """

        program, program_config_value, ac3file = self.__get_program(filename)
        if program < 0:
            return None, None, program_config_value 
       
        # get list of cuts
        error = cutlist.read_cuts()        
        if error:
            return None, None, error       
            
        if not cutlist.cuts_frames:                        
            fps, error = self.__get_fps(filename)
            if not error:
                cutlist.fps = fps
            else:
                return None, None, "Konnte FPS nicht bestimmen: " + error
            
            print "Calculate frame values from seconds."
            for start, duration in cutlist.cuts_seconds:
                cutlist.cuts_frames.append((start * cutlist.fps, duration * cutlist.fps))
               
        if program == Program.AVIDEMUX:
            cut_video, error = self.__cut_file_avidemux(filename, program_config_value, cutlist.cuts_frames)
            
        else: # VIRTUALDUB                              
            cut_video, error = self.__cut_file_virtualdub(filename, program_config_value, cutlist.cuts_frames)
            
        if error:
            return None, None, error
        elif ac3file != None:
	    return self.__mux_ac3(filename, cut_video, ac3file, cutlist)
	else:
            return cut_video, "", None
            
    def __mux_ac3(self, filename, cut_video, ac3_file, cutlist):	# cuts the ac3 and muxes it with the avi into an mkv
        mkvmerge = self.config.get('general', 'merge_ac3s_by')
	root, extension = splitext(filename)
	mkv_file = splitext(cut_video)[0] + ".mkv"
	# creates the timecodes string for splitting the .ac3 with mkvmerge
	timecodes = (','.join([self.__get_timecode(start) + ',' + self.__get_timecode(start+duration) for start, duration in cutlist.cuts_seconds]))
	# splitting .ac3. Every second fragment will be used.
	return_value = subprocess.call([mkvmerge, "--split", "timecodes:" + timecodes, "-o", root + "-%03d.mka", ac3_file])
	# return_value=0 is OK, return_value=1 means a warning. Most probably non-ac3-data that has been omitted.
        # TODO: Is there some way to pass this warning to the conclusion dialog?
        if return_value != 0 and return_value != 1:
            return None, None, str(return_value)
           
        if len(cutlist.cuts_seconds) == 1:              # Only the second fragment is needed. Delete the rest.
            fileoperations.rename_file(root + "-002.mka", root + ".mka")
            fileoperations.remove_file(root + "-001.mka")
            if os.path.isfile(root + "-003.mka"):
		fileoperations.remove_file(root + "-003.mka")
		
        else:                                           # Concatenating every second fragment.
            command = [mkvmerge, "-o", root + ".mka", root + "-002.mka"]
            command[len(command):] = ["+" + root + "-%03d.mka" % (2*n) for n in range(2,len(cutlist.cuts_seconds)+1)]
            return_value = subprocess.call(command)
            if return_value != 0:               # There should be no warnings here
                return None, None, str(return_value)
 
            for n in range(1,2*len(cutlist.cuts_seconds)+2):    # Delete all temporary audio fragments
		if os.path.isfile(root + "-%03d.mka" % n):
		    fileoperations.remove_file(root + "-%03d.mka" % n)
 
        # Mux the cut .avi with the resulting audio-file into mkv_file
        # TODO: Is there some way to pass possible warnings to the conclusion dialog?
        return_value = subprocess.call([mkvmerge, "-o", mkv_file, cut_video, root + ".mka"])
        if return_value != 0 and return_value != 1:
            return None, None, str(return_value)
        
        fileoperations.remove_file(root + ".mka")       # Delete remaining temporary files
        fileoperations.remove_file(cut_video)
        return mkv_file, ac3_file, None

    def __get_timecode(self, time):           # converts the seconds into a timecode-format that mkvmerge understands
        minute, second = divmod(int(time),60)		# discards milliseconds
        hour, minute = divmod(minute, 60)
        second = time - minute * 60 - hour * 3600	# for the milliseconds
        return "%02i:%02i:%f" % (hour, minute, second)

    def __cut_file_avidemux(self, filename, config_value, cuts):
        # make file for avidemux scripting engine
        f = open("tmp.js", "w")
                    
        f.writelines([
            '//AD\n',
            'var app = new Avidemux();\n',
            '\n'
            '//** Video **\n',            
            'app.load("%s");\n' % filename,            
            '\n',            
            'app.clearSegments();\n'
            ])
            
        for frame_start, frames_duration in cuts:
            f.write("app.addSegment(0, %i, %i);\n" %(frame_start, frames_duration))

        cut_video = self.__generate_filename(filename)
                                
        f.writelines([
            '//** Postproc **\n',
            'app.video.setPostProc(3,3,0);\n'
            ])
            
        if self.config.get('general', 'smart'):
            f.write('app.video.codec("Copy","CQ=4","0");\n')
            
        f.writelines([
            '//** Audio **\n',
            'app.audio.reset();\n',
            'app.audio.codec("copy",128,0,"");\n',
            'app.audio.normalizeMode=0;\n',
            'app.audio.normalizeValue=0;\n',
            'app.audio.delay=0;\n',
            'app.audio.mixer="NONE";\n',
            'app.audio.scanVBR="";\n',
            'app.setContainer="AVI";\n',
            'setSuccess(app.save("%s"));\n' % cut_video
            ])

        f.close()
        
        # start avidemux: 
        try:
            avidemux = subprocess.Popen([config_value, "--nogui", "--force-smart", "--run", "tmp.js", "--quit"], stderr=subprocess.PIPE)
        except OSError:
            return None, "Avidemux konnte nicht aufgerufen werden: " + config_value
        
        self.__gui.main_window.set_tasks_progress(50)
        
        while avidemux.poll() == None:
            time.sleep(1)
#            TODO: make it happen
#            line = avidemux.stderr.readline()
#
#            if "Done:" in line:
#                progress = line[line.find(":") + 1 : line.find("%")]
#                self.__gui.main_window.set_tasks_progress(int(progress))
#            
            while events_pending():
                main_iteration(False)
        
        fileoperations.remove_file('tmp.js')
        
        return cut_video, None
        
    def __cut_file_virtualdub(self, filename, config_value, cuts=None, manually=False):
        format, ac3_file = self.__get_format(filename)         

        if format == Format.HQ:
            if self.config.get('general', 'h264_codec') == 'ffdshow':    
                aspect, error_message = self.__get_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                     
                if aspect == "16:9":
                    comp_data = codec.get_comp_data_h264_169()
                else:
                    comp_data = codec.get_comp_data_h264_43()
                compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'x264vfw':
                aspect, error_message = self.__get_sample_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                   
                comp_data = codec.get_comp_data_x264vfw_dynamic(aspect,self.config.get('general', 'x264vfw_hq_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'komisar':
                aspect, error_message = self.__get_sample_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                    
                comp_data = codec.get_comp_data_komisar_dynamic(aspect,self.config.get('general', 'komisar_hq_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            else:
                return None, "Codec nicht unterstützt. Nur ffdshow, x264vfw und komisar unterstützt."

        elif format == Format.HD:
            if self.config.get('general', 'h264_codec') == 'ffdshow':    
                aspect, error_message = self.__get_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                     

                if aspect == "16:9":
                    comp_data = codec.get_comp_data_hd_169()
                else:
                    comp_data = codec.get_comp_data_hd_43()
                compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'x264vfw':
                aspect, error_message = self.__get_sample_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                     
                comp_data = codec.get_comp_data_x264vfw_dynamic(aspect,self.config.get('general', 'x264vfw_hd_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            elif self.config.get('general', 'h264_codec') == 'komisar':
                comp_data = codec.get_comp_data_komisar_dynamic(aspect,self.config.get('general', 'komisar_hd_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
            else:
                return None, "Codec nicht unterstützt. Nur ffdshow, x264vfw und komisar unterstützt."

        elif format == Format.MP4:
            if self.config.get('general', 'h264_codec') == 'komisar':
                aspect, error_message = self.__get_sample_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                     
                comp_data = codec.get_comp_data_komsiar_dynamic(aspect,self.config.get('general', 'komisar_mp4_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'
	    else: 
                aspect, error_message = self.__get_sample_aspect_ratio(filename)
                if not aspect:
                    return None, error_message                     
                comp_data = codec.get_comp_data_x264vfw_dynamic(aspect,self.config.get('general', 'x264vfw_mp4_string'))
                compression = 'VirtualDub.video.SetCompression(0x34363278,0,10000,0);\n'

        elif format == Format.AVI:      
            comp_data = codec.get_comp_data_dx50()
            compression = 'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
        
        else:
            return None, "Format nicht unterstützt (Nur Avi DX50, HQ H264 und HD sind möglich)."
        
        # make file for virtualdub scripting engine
        if manually:
            # TODO: kind of a hack
            curr_dir = os.getcwd()
            try:
                os.chdir(dirname(config_value))
            except OSError:        
                return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value
    
        self.__gui.main_window.set_tasks_progress(50)
    
        f = open("tmp.vcf", "w")
        
        if not manually:
            f.write('VirtualDub.Open("%s");\n' % filename)
            
        if self.config.get('general', 'smart'):
            f.writelines([               
                'VirtualDub.video.SetMode(1);\n',
                'VirtualDub.video.SetSmartRendering(1);\n',
                compression,
                'VirtualDub.video.SetCompData(%s);\n' % comp_data                
                ])
        else:
            f.write('VirtualDub.video.SetMode(0);\n')

        f.write('VirtualDub.subset.Clear();\n')

        if not manually:
            for frame_start, frames_duration in cuts:
                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start, frames_duration))

            cut_video = self.__generate_filename(filename,1)
                                
            f.writelines([
                'VirtualDub.SaveAVI("%s");\n' % cut_video,
                'VirtualDub.Close();'
                ])

        f.close()
        
        # start vdub
        if not exists(config_value):
            return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value
        
        if manually: 
            win_filename = "Z:" + filename.replace(r"/", r"\\")
            command = 'VirtualDub.exe /s tmp.vcf "%s"' % win_filename
        else:
            command = "%s /s tmp.vcf /x" % config_value

        if 'intern-VirtualDub' in config_value:
            command = 'WINEPREFIX=' + dirname(config_value) + '/wine' + " wineconsole " + command               
        else:
            command = "wineconsole " + command               
	  
        print command
        
        try:     
            vdub = subprocess.Popen(command, shell=True)
        except OSError:
            return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value
            
        while vdub.poll() == None:          
            time.sleep(1)
                      
            while events_pending():
                main_iteration(False)
        
        fileoperations.remove_file('tmp.vcf')
        
        if manually:
            os.chdir(curr_dir)            
            return None, None        

        return cut_video, None
