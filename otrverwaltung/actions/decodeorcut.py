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

from otrverwaltung import fileoperations
from otrverwaltung.filesconclusion import FileConclusion
from otrverwaltung.constants import Action, Cut_action, Status, Format, Program
from otrverwaltung.actions.baseaction import BaseAction
from otrverwaltung import codec
from otrverwaltung import cutlists as cutlists_management
from otrverwaltung import path
from otrverwaltung.GeneratorTask import GeneratorTask

class DecodeOrCut(BaseAction):
    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, action, filenames, config, rename_by_schema, cut_action=None):
        self.config = config
        self.rename_by_schema = rename_by_schema
        
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
 
                    
        # show conclusion
        file_conclusions = self.__gui.dialog_conclusion._run(file_conclusions, action, self.rename_by_schema, self.config.get('folder_archive'))       
                      
        if cut:
             
            # create cutlists            
            cutlists = []
            
            for file_conclusion in file_conclusions:

                if file_conclusion.cut.create_cutlist:
                    if "VirtualDub" in file_conclusion.cut.cutlist.intended_app:
                        intended_app_name = "VirtualDub"
                    else:
                        intended_app_name = "Avidemux"

                    file_conclusion.cut.cutlist.local_filename = file_conclusion.uncut_video + ".cutlist"
                    file_conclusion.cut.cutlist.author = self.config.get('cutlist_username')
                    file_conclusion.cut.cutlist.intended_version = open(path.getdatapath("VERSION"), 'r').read().strip()
                    file_conclusion.cut.cutlist.smart = self.config.get('smart')                   

                    file_conclusion.cut.cutlist.write_local_cutlist(file_conclusion.uncut_video, intended_app_name, file_conclusion.cut.my_rating)
                    
                    cutlists.append(file_conclusion.cut.cutlist)
                        
            # upload them:
            def upload():
                error_messages = []

                for cutlist in cutlists:
                    error_message = cutlist.upload(self.config.get('server'), self.config.get('cutlist_hash'))
                    if error_message: 
                        error_messages.append(error_message)
                    else:
                        if self.config.get('delete_cutlists'):
                            fileoperations.remove_file(cutlist.local_filename)
                 
                count = len(cutlists)
                
                message = "Es wurden %s/%s Cutlisten hochgeladen!" % (str(count - len(error_messages)), str(count))
                if len(error_messages) > 0:
                    message += " (" + ", ".join(error_messages) + ")"

                yield message

            if len(cutlists) > 0:
                if self.__gui.question_box("Soll(en) %s Cutlist(en) hochgeladen werden?" % len(cutlists)):
                    
                    def change_status(message):
                        self.__gui.main_window.change_status(0, message)
                    
                    GeneratorTask(upload, change_status).start()
            
            # rename
            for file_conclusion in file_conclusions:                         
                if file_conclusion.cut.rename:
                    extension = file_conclusion.get_extension()
                    if not file_conclusion.cut.rename.endswith(extension):
                        file_conclusion.cut.rename += extension
                
                    new_filename = join(self.config.get('folder_cut_avis'), file_conclusion.cut.rename.replace('/', '_'))
                    new_filename = fileoperations.make_unique_filename(new_filename)
                    
                    if file_conclusion.cut_video != new_filename:
                        file_conclusion.cut_video = fileoperations.rename_file(file_conclusion.cut_video, new_filename)
        
            # move cut video to archive
            for file_conclusion in file_conclusions:
                if file_conclusion.cut.archive_to:
                    fileoperations.move_file(file_conclusion.cut_video, file_conclusion.cut.archive_to)
        
            # move uncut video to trash if it's ok
            for file_conclusion in file_conclusions:
                if file_conclusion.cut.status == Status.OK and file_conclusion.cut.delete_uncut:
                    # move to trash
                    target = self.config.get('folder_trash_avis')
                    fileoperations.move_file(file_conclusion.uncut_video, target)        
        
            # remove local cutlists      
            if self.config.get('delete_cutlists'):
                for file_conclusion in file_conclusions:
                    if file_conclusion.cut.cutlist.local_filename and not file_conclusion.cut.create_cutlist: #and file_conclusion.cut.status == Status.OK:
                        if exists(file_conclusion.cut.cutlist.local_filename):
                            fileoperations.remove_file(file_conclusion.cut.cutlist.local_filename)
        
            # rate cutlists        
            def rate():                    
                yield 0 # fake generator
                messages = []
                count = 0
                for file_conclusion in file_conclusions:                    
                    if file_conclusion.cut.my_rating > -1:
                        print "Rate with ", file_conclusion.cut.my_rating
                        success, message = file_conclusion.cut.cutlist.rate(file_conclusion.cut.my_rating, self.config.get('server'))
                        if success:
                            count += 1
                        else:
                            messages += [message]
                
                if count > 0 or len(messages) > 0:
                    if count == 0:
                        text = "Es wurde keine Cutlist bewertet!"
                    if count == 1:
                        text = "Es wurde 1 Cutlist bewertet!"
                    else:
                        text = "Es wurden %s Cutlisten bewertet!" % count
                        
                    if len(messages) > 0:
                        text += " (Fehler: %s)" % ", ".join(messages)
                
                    self.__gui.main_window.change_status(0, text)
            
            GeneratorTask(rate).start()
             
     
    def decode(self, file_conclusions):          
            
        # no decoder        
        if not "decode" in self.config.get('decoder'): # no decoder specified
            # dialog box: no decoder
            self.__gui.message_error_box("Es ist kein korrekter Dekoder angegeben!")
            return False
        
        # retrieve email and password
        email = self.config.get('email')
        password = base64.b64decode(self.config.get('password')) 

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

            command = [self.config.get('decoder'), "-i", file_conclusion.otrkey, "-e", email, "-p", password, "-o", self.config.get('folder_uncut_avis')]
                      
            if not self.config.get('verify_decoded'):
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
                
                file_conclusion.uncut_video = join(self.config.get('folder_uncut_avis'), basename(file_conclusion.otrkey[0:len(file_conclusion.otrkey)-7]))
                             
                # move otrkey to trash
                target = self.config.get('folder_trash_otrkeys')
                fileoperations.move_file(file_conclusion.otrkey, target)
            else:            
                file_conclusion.decode.status = Status.ERROR
                file_conclusion.decode.message = error_message
                
        return True
            
    def cut(self, file_conclusions, action, default_cut_action=None):                      
        # now this method may not return "False"
        self.__gui.main_window.set_tasks_visible(True)
        self.__gui.main_window.block_gui(True)          
             
        if not default_cut_action:
            default_cut_action = self.config.get('cut_action')                                         
               
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
                    self.config.get('folder_cut_avis'),
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
               
                GeneratorTask(cutlists_management.download_cutlists, None, completed).start(file_conclusion.uncut_video, self.config.get('server'), self.config.get('choose_cutlists_by'), self.config.get('cutlist_mp4_as_hq'), error_cb, cutlist_found_cb)
                
                response = self.__gui.dialog_cut.run()                
                self.__gui.dialog_cut.hide()

                if response < 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen."                    
                else:  # change cut_action accordingly
                    file_conclusion.cut.cut_action = response

            if file_conclusion.cut.cut_action == Cut_action.MANUALLY: # MANUALLY                               
                error_message, cuts, executable = self.cut_file_manually(file_conclusion.uncut_video)
                                       
                if not error_message:
                    file_conclusion.cut.create_cutlist = True            
                    file_conclusion.cut.cutlist.cuts_frames = cuts
                    file_conclusion.cut.cutlist.intended_app = basename(executable)                    
                    
                    fps, error = self.__get_fps(file_conclusion.uncut_video)
                    if not error:
                        file_conclusion.cut.cutlist.fps = fps
                    else:
                        file_conclusion.cut.cutlist.fps = 25.
                        print "Achtung! Möglicherweise wurde eine falsche Fps-Anzahl eingetragen! (%s)" % error
                    # calculate seconds
                    for start_frame, duration_frames in cuts:
                        file_conclusion.cut.cutlist.cuts_seconds.append((start_frame / fps, duration_frames / fps))
                else:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error_message
                    
            elif file_conclusion.cut.cut_action == Cut_action.BEST_CUTLIST:
                error, cutlists = cutlists_management.download_cutlists(file_conclusion.uncut_video, self.config.get('server'), self.config.get('choose_cutlists_by'), self.config.get('cutlist_mp4_as_hq'))
                
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
        for count, file_conclusion in enumerate(file_conclusions):            
            
            if file_conclusion.cut.status in [Status.NOT_DONE, Status.ERROR]:
                continue    
        
            print "[Decodeandcut] Datei %s wird geschnitten" % file_conclusion.uncut_video
            self.__gui.main_window.set_tasks_text("Datei %s/%s schneiden" % (count + 1, len(file_conclusions)))
            self.__gui.main_window.set_tasks_progress(0.5)
            
            # download cutlist
            if file_conclusion.cut.cut_action in [Cut_action.BEST_CUTLIST, Cut_action.CHOOSE_CUTLIST]:
                file_conclusion.cut.cutlist.download(self.config.get('server'), file_conclusion.uncut_video)   

            cut_video, error = self.cut_file_by_cutlist(file_conclusion.uncut_video, file_conclusion.cut.cutlist)                

            if cut_video == None:
                file_conclusion.cut.status = Status.ERROR
                file_conclusion.cut.message = error    
            else:
                file_conclusion.cut.status = Status.OK
                file_conclusion.cut_video = cut_video
                
                if self.config.get('rename_cut'):                        
                    file_conclusion.cut.rename = self.rename_by_schema(basename(file_conclusion.uncut_video))
                else:
                    file_conclusion.cut.rename = basename(cut_video)               
        
        return True

    def __get_format(self, filename):        
        root, extension = splitext(filename)
            
        if extension == '.avi':
            if splitext(root)[1] == '.HQ':
                return Format.HQ
            elif splitext(root)[1] == '.HD':
                return Format.HD
            else:
                return Format.AVI
        elif extension == '.mp4':
            return Format.MP4
        else:
            return -1

    def __get_program(self, filename, manually=False):   
        if manually:
            programs = { Format.AVI : self.config.get('cut_avis_man_by'),
                         Format.HQ  : self.config.get('cut_hqs_man_by'),
                         Format.HD  : self.config.get('cut_hqs_man_by'),
                         Format.MP4 : self.config.get('cut_mp4s_man_by') }
        else:
            programs = { Format.AVI : self.config.get('cut_avis_by'),
                         Format.HQ  : self.config.get('cut_hqs_by'),
                         Format.HD  : self.config.get('cut_hqs_by'),                         
                         Format.MP4 : self.config.get('cut_mp4s_by') }
                     
        format = self.__get_format(filename)                 

        if format < 0:
            return -1, "Format konnte nicht bestimmt werden/wird noch nicht unterstützt."
                             
        config_value = programs[format]
        
        if 'avidemux' in config_value:
            return Program.AVIDEMUX, config_value
        elif 'vdub' in config_value or 'VirtualDub' in config_value:
            return Program.VIRTUALDUB, config_value
        else:
            return -2, "Programm '%s' konnte nicht bestimmt werden. Es werden VirtualDub und Avidemux unterstützt." % config_value
   
    def __generate_filename(self, filename):
        """ generate filename for a cut video file. """
        
        root, extension = splitext(basename(filename))
                
        new_name = root + "-cut" + extension
                
        cut_video = join(self.config.get('folder_cut_avis'), new_name)        
            
        return cut_video
   
    def __get_fps(self, filename):
        """ Gets the fps of a movie using mplayer. 
            Returns without error:              
                       fps, None
                    with error:
                       None, error_message """
        
        mplayer = self.config.get('mplayer')
            
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
        mplayer = self.config.get('mplayer')
            
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
            
    def __create_cutlist_virtualdub(self, filename):
        """ returns: cuts, error_message """
        
        try:
            f = open(filename, 'r')
        except IOError:
            return None, "Konnte %s nicht finden, um Cutlist zu erstellen." % filename

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
        """ Cuts a file manually with Avidemux or VirtualDub and gets cuts from
            possibly created project files (VD) or from output (AD). 
            returns: error_message, cuts, executable """
        
        program, config_value = self.__get_program(filename, manually=True)
        
        if program < 0:
            return config_value, None, None
            
        if program == Program.AVIDEMUX:       

            try:                   
                avidemux = subprocess.Popen([config_value, filename], stdout=subprocess.PIPE)
            except OSError:
                return "Avidemux konnte nicht aufgerufen werden: " + config_value, None, None
                
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
                        
        else: # VIRTUALDUB
            
            cut_video_is_none, error = self.__cut_file_virtualdub(filename, config_value, cuts=None, manually=True)
            
            if error != None:
                return error, None, None
                
            cuts_frames, cutlist_error = self.__create_cutlist_virtualdub(join(self.config.get('folder_uncut_avis'), "cutlist.vcf"))
         
        if cutlist_error:            
            return cutlist_error, None, config_value
        else:
            return None, cuts_frames, config_value
             
    def cut_file_by_cutlist(self, filename, cutlist):
        """ Returns: cut_video, error """

        program, program_config_value = self.__get_program(filename)
        if program < 0:
            return None, program_config_value 
       
        # get list of cuts
        error = cutlist.read_cuts()        
        if error:
            return None, error       
            
        if not cutlist.cuts_frames:                        
            fps, error = self.__get_fps(filename)
            if not error:
                cutlist.fps = fps
            else:
                return None, "Konnte FPS nicht bestimmen: " + error
            
            print "Calculate frame values from seconds."
            for start, duration in cutlist.cuts_seconds:
                cutlist.cuts_frames.append((start * cutlist.fps, duration * cutlist.fps))
               
        if program == Program.AVIDEMUX:
            cut_video, error = self.__cut_file_avidemux(filename, program_config_value, cutlist.cuts_frames)
            
        else: # VIRTUALDUB                              
            cut_video, error = self.__cut_file_virtualdub(filename, program_config_value, cutlist.cuts_frames)
            
        if error:
            return None, error
        else:
            return cut_video, None

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
            
        if self.config.get('smart'):
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
            avidemux = subprocess.Popen([config_value, "--force-smart", "--run", "tmp.js", "--quit"], stderr=subprocess.PIPE)
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
        format = self.__get_format(filename)         

        if format == Format.HQ:
            aspect, error_message = self.__get_aspect_ratio(filename)
            if not aspect:
                return None, error_message                     
                
            if aspect == "16:9":
                comp_data = codec.get_comp_data_h264_169()
            else:
                comp_data = codec.get_comp_data_h264_43()
        elif format == Format.HD:
            aspect, error_message = self.__get_aspect_ratio(filename)
            if not aspect:
                return None, error_message                     
                
            if aspect == "16:9":
                comp_data = codec.get_comp_data_hd_169()
            else:
                comp_data = codec.get_comp_data_hd_43()
        
        elif format == Format.AVI:      
            comp_data = codec.get_comp_data_dx50()
        
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
            
        if self.config.get('smart'):
            f.writelines([               
                'VirtualDub.video.SetMode(1);\n',
                'VirtualDub.video.SetSmartRendering(1);\n',
                'VirtualDub.video.SetCompression(0x53444646,0,10000,0);\n'
                'VirtualDub.video.SetCompData(%s);\n' % comp_data                
                ])
        else:
            f.write('VirtualDub.video.SetMode(0);\n')

        f.write('VirtualDub.subset.Clear();\n')

        if not manually:
            for frame_start, frames_duration in cuts:
                f.write("VirtualDub.subset.AddRange(%i, %i);\n" % (frame_start, frames_duration))

            cut_video = self.__generate_filename(filename)
                                
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
