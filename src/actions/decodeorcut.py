#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gtk import events_pending, main_iteration, RESPONSE_OK
import base64
import popen2
import subprocess
import urllib
import os
from os.path import basename, join, dirname, exists, splitext
import time

import fileoperations
from filesconclusion import FileConclusion
from constants import Action, Cut_action, Status, Format, Program
from baseaction import BaseAction
import codec
import cutlists as cutlists_management
import otrpath
from GeneratorTask import GeneratorTask

class DecodeOrCut(BaseAction):
    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, action, filenames, config, rename_by_schema, cut_action=None):
        self.config = config
        
        decode, cut = False, False            
            
        # prepare tasks
        self.__gui.main_window.get_widget('progressbar_tasks').set_fraction(0.0)

        if action == Action.DECODE:
            self.__gui.main_window.get_widget('label_tasks').set_text('Dekodieren')
            decode = True
        elif action == Action.CUT:
            self.__gui.main_window.get_widget('label_tasks').set_text('Schneiden')
            cut = True
        else: # decode and cut
            self.__gui.main_window.get_widget('label_tasks').set_text('Dekodieren/Schneiden')        
            decode, cut = True, True
                                       
        file_conclusions = []
            
        if decode:
            for otrkey in filenames:
                file_conclusions.append(FileConclusion(action, otrkey=otrkey))
            
        if cut and not decode: # dont add twice
            for uncut_avi in filenames:
                file_conclusions.append(FileConclusion(action, uncut_avi=uncut_avi))
                        
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
        self.__gui.main_window.get_widget('eventbox_tasks').hide()
                    
        # show conclusion
        dialog = self.__gui.dialog_conclusion.build(file_conclusions, action, rename_by_schema, self.config.get('rename_cut'))
        dialog.run()
        dialog.hide()         
        
        file_conclusions = self.__gui.dialog_conclusion.file_conclusions        
                      
        if cut:
             
            # create cutlists            
            cutlists = []
            
            for file_conclusion in file_conclusions:
                if file_conclusion.cut.create_cutlist and not file_conclusion.cut.create_cutlist_error:  

                    if "VirtualDub" in file_conclusion.cut.cutlist.intended_app:
                        intended_app_name = "VirtualDub"
                    else:
                        intended_app_name = "Avidemux"

                    file_conclusion.cut.cutlist.local_filename = file_conclusion.uncut_avi + ".cutlist"
                    file_conclusion.cut.cutlist.author = self.config.get('cutlist_username')
                    file_conclusion.cut.cutlist.intended_version = open(otrpath.get_path("VERSION"), 'r').read().strip()
                    file_conclusion.cut.cutlist.smart = self.config.get('smart')

                    file_conclusion.cut.cutlist.write_local_cutlist(file_conclusion.uncut_avi, intended_app_name, file_conclusion.cut.my_rating)
                    
                    cutlists.append(file_conclusion.cut.cutlist)
                        
            # upload them:            
            def upload(error_cb):
                yield 0 # fake generator                   
                errors = 0                
                userid = self.config.get('cutlist_hash')

                for cutlist in cutlists:
                    error_message = cutlist.upload(userid)
                    if error_message: 
                        error_cb("Fehler beim Hochladen der Cutlist:\n" + error_message)
                        errors += 1
                    else:
                        if self.config.get('delete_cutlists'):
                            fileoperations.remove_file(file_conclusion.cut.cutlist.local_filename)
                 
                count = len(cutlists)                       
                self.__gui.main_window.change_status(0, "Es wurden %s/%s Cutlisten hochgeladen!" % (str(count - errors), str(count)))                        
                
            if len(cutlists) > 0:                
                if self.__gui.question_box("Soll(en) %s Cutlist(en) hochgeladen werden?" % len(cutlists)):
                    
                    def error_cb(self, message):
                        self.__gui.message_error_box(message)
                    
                    GeneratorTask(upload).start(error_cb)
            
            # rename
            for file_conclusion in file_conclusions:
           
                rename = file_conclusion.cut.rename                                                          
                
                # TODO: mp4 support
            
                if 0 == rename: # no rename
                    continue
                    
                elif 1 == rename: # otr rename                               
                    new_name = rename_by_schema(basename(file_conclusion.uncut_avi))
            
                elif 2 == rename: # filename rename
                    new_name = file_conclusion.cut.cutlist.filename + ".avi"
                    
                elif 3 == rename: # filename_original rename
                    new_name = file_conclusion.cut.cutlist.filename_original + ".avi"
                    
                elif 4 == rename: # autoname rename
                    new_name = file_conclusion.cut.cutlist.autoname + ".avi"                    
            
                new_filename = join(self.config.get('folder_cut_avis'), new_name)        
                fileoperations.rename_file(file_conclusion.cut_avi, new_filename)                
        
            # move uncut avi to trash if it's ok            
            for file_conclusion in file_conclusions:
                if file_conclusion.cut.status == Status.OK and file_conclusion.cut.delete_uncut:
                    # move to trash
                    print file_conclusion.uncut_avi, " to trash"
                    target = self.config.get('folder_trash')
                    fileoperations.move_file(file_conclusion.uncut_avi, target)        
        
            # remove local cutlists      
            if self.config.get('delete_cutlists'):
                for file_conclusion in file_conclusions:
                    if file_conclusion.cut.cutlist.local_filename and not file_conclusion.cut.create_cutlist:
                        if exists(file_conclusion.cut.cutlist.local_filename):
                            fileoperations.remove_file(file_conclusion.cut.cutlist.local_filename)
        
            # rate cutlists        
            def rate():                    
                yield 0 # fake generator
                count = 0
                for file_conclusion in file_conclusions:                    
                    if file_conclusion.cut.my_rating:
                        print "Rate!"
                        if file_conclusion.cut.cutlist.rate(file_conclusion.cut.my_rating, self.config.get('server')):
                            count += 1
                
                if count > 0:
                    self.__gui.main_window.change_status(0, "Es wurde(n) %s Cutlist(en) bewertet!" % count)              
            
            GeneratorTask(rate).start()
             
     
    def decode(self, file_conclusions):          
            
        # no decoder        
        if not "decode" in self.config.get('decoder'): # no decoder specified
            # dialog box: no decoder
            self.__gui.message_error_box("Es ist kein korrekter Dekoder angegeben!")
            return False
        
        # retrieve email and password
        # user did not save email and password
        if not self.config.get('save_email_password'):
            # let the user type in his data through a dialog
            response = self.__gui.dialog_email_password.run()
            self.__gui.dialog_email_password.hide() 
            
            if response==RESPONSE_OK:
                email = self.__gui.dialog_email_password.get_widget('entryDialogEMail').get_text()
                password = self.__gui.dialog_email_password.get_widget('entryDialogPassword').get_text()                               
            else: # user pressed cancel
                return False
                         
        else: # user typed email and password in         
            email = self.config.get('email')
            password = base64.b64decode(self.config.get('password')) 
        
        # now this method may not return "False"
        self.__gui.main_window.get_widget('eventbox_tasks').show()
        self.__gui.main_window.block_gui(True)
                   
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
            # update progress
            self.__gui.main_window.get_widget('label_tasks').set_text("Datei %s/%s dekodieren" % (count + 1, len(file_conclusions)))
                   
            verify = True
                   
            curr_dir = ""      
            if os.name == "posix":
                command = "%s -i %s -e %s -p %s -o %s" % (self.config.get('decoder'), file_conclusion.otrkey, email, password, self.config.get('folder_uncut_avis'))
            
                if self.config.get('verify_decoded') == 0:
                    verify = False
                    command += " -q"
            
            else: # windows
                verify = False
               
                # TODO: de-hack, use subprocess module and get rid of while events_pending()...
                curr_dir = os.getcwd()   
                os.chdir(dirname(self.config.get('decoder')))

                command = '%s -uotr %s -pwotr %s -f %s -o %s -c true -hide' % (basename(self.config.get('decoder')), email, password, file_conclusion.otrkey, self.config.get('folder_uncut_avis'))                              

            (pout, pin, perr) = popen2.popen3(command)
            if os.name == "posix":
                while True:
                    l = ""
                    while True:
                        c = pout.read(1)
                        if c == "\r" or c == "\n":
                            break
                        l += c
            
                    if not l:
                        break
            
                    try:                             
                        if verify:   
                            file_count = count + 1, len(file_conclusions)
                                                           
                            if "input" in l:
                                self.__gui.main_window.get_widget('label_tasks').set_text("Eingabedatei %s/%s kontrollieren" % file_count)
                            elif "output" in l:
                                self.__gui.main_window.get_widget('label_tasks').set_text("Ausgabedatei %s/%s kontrollieren" % file_count)
                            elif "Decoding" in l:
                                self.__gui.main_window.get_widget('label_tasks').set_text("Datei %s/%s dekodieren" % file_count)
                                                           
                        progress = int(l[10:13])                    
                        # update progress
                        self.__gui.main_window.get_widget('progressbar_tasks').set_fraction(progress / 100.)
                        
                        while events_pending():
                            main_iteration(False)
                    except ValueError:                
                        pass

            if curr_dir:
               os.chdir(curr_dir)
            
            # errors?
            errors = perr.readlines()
            error_message = ""
            for error in errors:
                error_message += error.strip()
                            
            # close process
            pout.close()
            perr.close()
            pin.close()
                                                            
            if len(errors) == 0: # dekodieren erfolgreich                
                file_conclusion.decode.status = Status.OK
                print self.config.get('folder_uncut_avis')
                print file_conclusion.otrkey
                print basename(file_conclusion.otrkey)[0:len(file_conclusion.otrkey)-7]
                file_conclusion.uncut_avi = join(self.config.get('folder_uncut_avis'), basename(file_conclusion.otrkey[0:len(file_conclusion.otrkey)-7]))
                             
                # move otrkey to trash
                target = self.config.get('folder_trash')
                fileoperations.move_file(file_conclusion.otrkey, target)
            else:            
                file_conclusion.decode.status = Status.ERROR
                file_conclusion.decode.message = error_message
                
        return True
            
    def cut(self, file_conclusions, action, cut_action=None):                      
        # now this method may not return "False"
        self.__gui.main_window.get_widget('eventbox_tasks').show()
        self.__gui.main_window.block_gui(True)  
        
        for count, file_conclusion in enumerate(file_conclusions):
            self.__gui.main_window.get_widget('label_tasks').set_text("Datei %s/%s schneiden" % (count + 1, len(file_conclusions)))
            self.__gui.main_window.get_widget('progressbar_tasks').set_fraction(0.0)
    
            # file correctly decoded?            
            if action == Action.DECODEANDCUT:
                if file_conclusion.decode.status == Status.ERROR:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Datei wurde nicht dekodiert."
                    continue

            # how should the file be cut?
            if not cut_action:
                cut_action = self.config.get('cut_action')
                
            cutlists = []
            
            if cut_action == Cut_action.MANUALLY:
                pass

            elif cut_action == Cut_action.LOCAL_CUTLIST:
                pass

            elif cut_action == Cut_action.BEST_CUTLIST:                

                def error_cb(error):
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = error

                cutlists = cutlists_management.download_cutlists(file_conclusion.uncut_avi, self.config.get('server'), self.config.get('choose_cutlists_by'), error_cb)
                
                if len(cutlists) == 0:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = "Keine Cutlists gefunden!"          
                    continue
                             
            else:  # ASK, CHOOSE_CUTLIST
                # show dialog
                self.__gui.dialog_cut.filename = file_conclusion.uncut_avi
                self.__gui.dialog_cut.get_widget('label_file').set_markup("<b>%s</b>" % basename(file_conclusion.uncut_avi))
                self.__gui.dialog_cut.get_widget('label_warning').set_markup('<span size="small">Wichtig! Die Datei muss im Ordner "%s" und unter einem neuen Namen gespeichert werden, damit das Programm erkennt, dass diese Datei geschnitten wurde!\n\nUm eine Cutlist zu erstellen muss das Projekt gespeichert werden (siehe Website->Wiki->Häufige Fragen).</span>' % self.config.get('folder_cut_avis'))

                if cut_action == Cut_action.ASK:
                    self.__gui.dialog_cut.get_widget('radio_best_cutlist').set_active(True)
                else:
                    self.__gui.dialog_cut.get_widget('radio_choose_cutlist').set_active(True)

                # looking for a local cutlist
                filename_cutlist = file_conclusion.uncut_avi + ".cutlist"
                if exists(filename_cutlist):
                    self.__gui.dialog_cut.get_widget('label_cutlist').set_markup("<b>%s</b>" % filename_cutlist)
                    self.__gui.dialog_cut.get_widget('radio_local_cutlist').set_sensitive(True)
                else:
                    self.__gui.dialog_cut.get_widget('label_cutlist').set_markup("Keine lokale Cutlist gefunden.")
                    self.__gui.dialog_cut.get_widget('radio_local_cutlist').set_sensitive(False)

                # start looking for cutlists
                self.__gui.dialog_cut.get_widget('treeview_cutlists').get_model().clear()                
                self.__gui.dialog_cut.get_widget('label_status').set_markup("<b>Cutlisten werden heruntergeladen...</b>")
                              
                self.cutlists_error = False
                
                def error_cb(error):            
                    self.__gui.dialog_cut.get_widget('label_status').set_markup("<b>%s</b>" % error)
                    self.cutlists_error = True
                     
                def cutlist_found_cb(cutlist):
                    self.__gui.dialog_cut.add_cutlist(cutlist)
                    cutlists.append(cutlist)
               
                def completed():
                    if not self.cutlists_error:
                        self.__gui.dialog_cut.get_widget('label_status').set_markup("")
               
                GeneratorTask(cutlists_management.download_cutlists, cutlist_found_cb, completed).start(file_conclusion.uncut_avi, self.config.get('server'), self.config.get('choose_cutlists_by'), error_cb)
                
                response = self.__gui.dialog_cut.run()                
                self.__gui.dialog_cut.hide()

                print "response", response

                if response < 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen"
                    continue
                else:
                    cut_action = response
                    
            # save cut_action
            file_conclusion.cut.cut_action = cut_action

            if cut_action == Cut_action.MANUALLY: # MANUALLY                               
                error_code, error_message, cuts, executable = self.cut_file_manually(file_conclusion.uncut_avi)
                                       
                if error_code < 0:
                    file_conclusion.cut.status = Status.OK  
                    file_conclusion.cut.create_cutlist = True            
                    file_conclusion.cut.cutlist.cuts = cuts
                    file_conclusion.cut.cutlist.intended_app = basename(executable)
                    # do not continue because the file isn't cut already!
                    
                elif error_code == 1:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error_message                   
                    continue

                elif error_code == 2:                    
                    file_conclusion.cut.status = Status.OK                         
                    file_conclusion.cut.create_cutlist_error = error_message                    
                    continue               
                    
            # all other cases and if we got cuts: cut file by cutlist

            if cut_action == Cut_action.BEST_CUTLIST:
                if len(cutlists) == 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Keine Cutlist gefunden"
                    continue
                                               
                file_conclusion.cut.cutlist = cutlists_management.get_best_cutlist(cutlists)                                 
                file_conclusion.cut.cutlist.download(self.config.get('server'), file_conclusion.uncut_avi)
             
            elif cut_action == Cut_action.CHOOSE_CUTLIST:
                
                file_conclusion.cut.cutlist = self.__gui.dialog_cut.chosen_cutlist
                file_conclusion.cut.cutlist.download(self.config.get('server'), file_conclusion.uncut_avi)
                
            elif cut_action == Cut_action.LOCAL_CUTLIST:     
                file_conclusion.cut.cutlist.local_filename = file_conclusion.uncut_avi + ".cutlist"
                
                if not exists(file_conclusion.cut.cutlist.local_filename):
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = "Keine lokale Cutlist gefunden."
                    continue
            
            # and finally cut the file
            cut_avi, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, file_conclusion.cut.cutlist)

            if cut_avi == None:
                file_conclusion.cut.status = Status.ERROR
                file_conclusion.cut.message = error    
            else:
                file_conclusion.cut.status = Status.OK
                file_conclusion.cut_avi = cut_avi                    
                                                        
        # after iterating over all items:
        return True

    def __get_format(self, filename):        
        root, extension = splitext(filename)
            
        if extension == '.avi':
            if splitext(root)[1] == '.HQ':
                return Format.HQ
            else:
                return Format.AVI
        elif extension == '.mp4':
            # TODO: mp4 support
            return -1
            return Format.MP4
        else:
            return -1

    def __get_program(self, filename, manually=False):   
        if manually:
            programs = { Format.AVI : self.config.get('cut_avis_man_by'),
                         Format.HQ  : self.config.get('cut_hqs_man_by') }
        else:
            programs = { Format.AVI : self.config.get('cut_avis_by'),
                         Format.HQ  : self.config.get('cut_hqs_by') }
                     
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
        # generate filename for a cut avi
        name = basename(filename)
        
        #TODO: mp4 support
        new_name = name[0:len(name)-4] # remove .avi
        new_name += "-cut.avi"
                
        cut_avi = join(self.config.get('folder_cut_avis'), new_name)        
            
        return cut_avi
   
    def __get_aspect_ratio(self, filename):
        """ Gets the aspect ratio of a movie using mplayer. 
            Returns without error:              
                       aspect_ratio, None
                    with error:
                       None, error_message """
        
        mplayer = self.config.get('mplayer')
        
        if not mplayer:
            return None, "Der Mplayer ist nicht angegeben. Dieser wird zur Bestimmung der Aspect Ratio benötigt."
        
        try:
            process = subprocess.Popen([mplayer, "-vo", "null", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
        except OSError:
            return None, "MPlayer wurde nicht gefunden!"            
           
        while True:
            line = process.stdout.readline()
                    
            if process.poll() != None:
                time.sleep(1)
            
                return None, "Mplayer-Fehlermeldung: " + process.stderr.read()
        
            if "Aspe" in line:
                if "1.78:1" in line or "0.56:1" in line:
                    return "16:9", None
                elif "1.33:1" in line or "0.75:1" in line:
                    return "4:3", None
                else:
                    return None, "Aspekt konnte nicht bestimmt werden " + line
    
    def __create_cutlist_avidemux(self, filename):
        """ returns: cuts, error_message """
        
        try:
            f = open(filename, 'r')
        except IOError:
            return None, "Konnte %s nicht finden, um Cutlist zu erstellen." % filename

        cuts = [] # (count, start, duration)
        count = 0

        for line in f.readlines():
            if "app.addSegment" in line:
                try:
                    null, start, duration = line[line.index('(') + 1 : line.index(')')].split(',')
                except (IndexError, ValueError), message:
                    return None, "Konnte Schnitte nicht lesen, um Cutlist zu erstellen. (%s)" % message
                
                # convert to seconds (avidemux uses frames)
                cuts.append((count, int(start) / 25., int(duration) / 25.))
                
                count += 1

        fileoperations.remove_file(filename)

        if not cuts:
            return None, "Konnte keine Schnitte lesen."

        return cuts, None       
        
    def __create_cutlist_virtualdub(self, filename):
        """ returns: cuts, error_message """
        
        try:
            f = open(filename, 'r')
        except IOError:
            return None, "Konnte %s nicht finden, um Cutlist zu erstellen." % filename

        cuts = [] # (count, start, duration)
        count = 0

        for line in f.readlines():
            if "VirtualDub.subset.AddRange" in line:
                try:
                    start, duration = line[line.index('(') + 1 : line.index(')')].split(',')
                except (IndexError, ValueError), message:
                    return None, "Konnte Schnitte nicht lesen, um Cutlist zu erstellen. (%s)" % message
                
                cuts.append((count, int(start) / 25., int(duration) / 25. ))
                
                count += 1

        if len(cuts) == 0:
            return None, "Konnte keine Schnitte finden!"

        fileoperations.remove_file(filename)

        return cuts, None       
       
    def cut_file_manually(self, filename):
        """ Cuts a file manually with Avidemux or VirtualDub and gets cuts from
            possibly created project files. 
            returns: error_code, error_message, cuts, executable

            error_code: -1 - no error
                         1 - program (avidemux/VirtualDub) error 
                         2 - could not get cuts 
                         3 - could not cut by cutlist """
        
        program, config_value = self.__get_program(filename, manually=True)
        
        if program < 0:
            return 1, config_value, None, None
    
        if program == Program.AVIDEMUX:       
            script_filename = filename + ".js"
            
            f = open(script_filename, "w")
            
            f.writelines([
                '//AD\n',
                'var app = new Avidemux();\n',
                'app.load("%s");\n' % filename
            ])
            
            f.close()
            
            command = [config_value, "--run", script_filename]

            try:                   
                avidemux = subprocess.Popen(command)
            except OSError:
                return 1, "Avidemux konnte nicht aufgerufen werden: " + config_value, None, None
                
            while avidemux.poll() == None:
                time.sleep(1)
                pass
                
            cuts, cutlist_error = self.__create_cutlist_avidemux(join(self.config.get('folder_uncut_avis'), script_filename))                              
                        
        else: # VIRTUALDUB
            
            cut_avi_is_none, error = self.__cut_file_virtualdub(filename, config_value, cuts=None, manually=True)
            
            if error != None:
                return 1, error, None, None
                
            cuts, cutlist_error = self.__create_cutlist_virtualdub(join(self.config.get('folder_uncut_avis'), "cutlist.vcf"))
         
        if cutlist_error:            
            return 2, cutlist_error, None, config_value
        else:
            return -1, None, cuts, config_value
             
    def cut_file_by_cutlist(self, filename, cutlist):
        """ Returns: cut_avi, error """

        program, program_config_value = self.__get_program(filename)
        if program < 0:
            return None, program_config_value 
       
        # get list of cuts
        error = cutlist.read_cuts()        
        if error:
            return None, error       
        
        if program == Program.AVIDEMUX:
            cut_avi, error = self.__cut_file_avidemux(filename, program_config_value, cutlist.cuts)
            
        else: # VIRTUALDUB                              
            cut_avi, error = self.__cut_file_virtualdub(filename, program_config_value, cutlist.cuts)
            
        if error:
            return None, error
        else:
            return cut_avi, None

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
            
        for count, start, duration in cuts:
            frame_start = start * 25   
            frame_duration = duration * 25
            f.write("app.addSegment(0, %s, %s);\n" %(str(int(frame_start)), str(int(frame_duration))))

        cut_avi = self.__generate_filename(filename)
                                
        f.writelines([
            '//** Postproc **\n',
            'app.video.setPostProc(3,3,0);\n',
            'app.video.setFps1000(25000);\n'
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
            'app.audio.mixer("NONE");\n',
            'app.audio.scanVBR();\n',
            'app.setContainer("AVI");\n',
            'setSuccess(app.save("%s"));\n' % cut_avi
            ])

        f.close()
        
        # start avidemux: 
        try:
            avidemux = subprocess.Popen([config_value, "--force-smart", "--run", "tmp.js", "--quit"], stderr=subprocess.PIPE)
        except OSError:
            return None, "Avidemux konnte nicht aufgerufen werden: " + config_value
        
        self.__gui.main_window.get_widget('progressbar_tasks').set_fraction(.5)
        
        while avidemux.poll() == None:
            time.sleep(1)
#            TODO: make it happen
#            line = avidemux.stderr.readline()
#
#            if "Done:" in line:
#                progress = line[line.find(":") + 1 : line.find("%")]
#                self.__gui.main_window.get_widget('progressbar_tasks').set_fraction(int(progress) / 100.)
#            
            while events_pending():
                main_iteration(False)
        
        fileoperations.remove_file('tmp.js')
        
        return cut_avi, None
        
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
                
        elif format == Format.AVI:      
            comp_data = codec.get_comp_data_dx50()
        else:
            return None, "Format nicht unterstützt (Nur Avi DX50 und HQ H264 sind möglich)."
        
        # make file for virtualdub scripting engine
        if manually:
            # TODO: kind of a hack
            curr_dir = os.getcwd()
            try:
                os.chdir(dirname(config_value))
            except OSError:        
                return None, "VirtualDub konnte nicht aufgerufen werden: " + config_value
    
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
            for count, start, duration in cuts:
                f.write("VirtualDub.subset.AddRange(%s, %s);\n" % (str(start * 25), str(duration * 25)))

            cut_avi = self.__generate_filename(filename)
                                
            f.writelines([
                'VirtualDub.SaveAVI("%s");\n' % cut_avi,
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

        if os.name == 'posix':
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

        return cut_avi, None
