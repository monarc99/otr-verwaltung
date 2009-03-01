#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gtk import events_pending, main_iteration, RESPONSE_OK
import gobject
import base64
import popen2
import subprocess
import urllib
import os
from os.path import basename, join, dirname, exists
import threading

import fileoperations
from filesconclusion import FileConclusion
from constants import Action, Cut_action, Save_Email_Password, Status
from baseaction import BaseAction
import cutlists as cutlists_management

class GeneratorTask(object):
   def __init__(self, generator, loop_callback, complete_callback=None):
       self.generator = generator
       self.loop_callback = loop_callback
       self.complete_callback = complete_callback

   def _start(self, *args, **kwargs):
       self._stopped = False
       for ret in self.generator(*args, **kwargs):
           if self._stopped:
               thread.exit()
           gobject.idle_add(self._loop, ret)
       if self.complete_callback is not None:
           gobject.idle_add(self.complete_callback)

   def _loop(self, ret):
       if ret is None:
           ret = ()
       if not isinstance(ret, tuple):
           ret = (ret,)
       self.loop_callback(*ret)

   def start(self, *args, **kwargs):
       threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

   def stop(self):
       self._stopped = True

class DecodeOrCut(BaseAction):
    
    def __init__(self, gui):
        self.update_list = True
        self.__gui = gui

    def do(self, action, filenames, config, rename_by_schema):
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
        else:
            self.__gui.main_window.get_widget('label_tasks').set_text('Dekodieren/Schneiden')
            decode, cut = True, True
                                    
        # create file_conclusions array        
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
            if self.cut(file_conclusions, action, rename_by_schema) == False: 
                return

        self.__gui.main_window.block_gui(False)

        # no more need for tasks view
        self.__gui.main_window.get_widget('eventbox_tasks').hide()
                    
        # show conclusion
        dialog = self.__gui.dialog_conclusion.build(file_conclusions, action)
        dialog.run()
        dialog.hide()         
        
        file_conclusions = self.__gui.dialog_conclusion.file_conclusions
        
        
        if cut:
        
            # move to trash if it's ok
            for file_conclusion in file_conclusions:
                if file_conclusion.cut.delete_uncut:
                    # move to trash
                    print file_conclusion.uncut_avi, " to trash"
                    target = self.config.get('folders', 'trash')
                    fileoperations.move_file(file_conclusion.uncut_avi, target)        
        
            # remove local cutlists      
            if self.config.get('cut', 'delete_cutlists'):
                for file_conclusion in file_conclusions:
                    if file_conclusion.cut.local_cutlist:
                        fileoperations.remove_file(file_conclusion.cut.local_cutlist)
        
            # rate cutlists
            if cut:
                count = 0
                for file_conclusion in file_conclusions:                    
                    if file_conclusion.cut.rating > -1:
                        if cutlists_management.rate(file_conclusion.cut.cutlist, file_conclusion.cut.rating, self.config.get('cut', 'server')):
                            count += 1
                
                if count == 1:
                    self.__gui.message_info_box("Es wurde 1 Cutlist bewertet!")
                elif count > 1:
                    self.__gui.message_info_box("Es wurden %s Cutlisten bewertet!" % count)
             
     
    def decode(self, file_conclusions):          
            
        # no decoder        
        if not "decode" in self.config.get('decode', 'path'): # no decoder specified
            # dialog box: no decoder
            self.__gui.message_error_box("Es ist kein korrekter Dekoder angegeben!")
            return False
        
        # retrieve email and password
        # user did not save email and password
        if self.config.get('decode', 'save_email_password') == Save_Email_Password.DONT_SAVE:
            # let the user type in his data through a dialog
            response = self.__gui.dialog_email_password.run()
            self.__gui.dialog_email_password.hide() 
            
            if response==RESPONSE_OK:
                email = self.__gui.dialog_email_password.get_widget('entryDialogEMail').get_text()
                password = self.__gui.dialog_email_password.get_widget('entryDialogPassword').get_text()                               
            else: # user pressed cancel
                return False
                         
        else: # user typed email and password in         
            email = self.config.get('decode', 'email')
            password = base64.b64decode(self.config.get('decode', 'password')) 
        
        # now this method may not return "False"
        self.__gui.main_window.get_widget('eventbox_tasks').show()
        self.__gui.main_window.block_gui(True)
                   
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
            # update progress
            self.__gui.main_window.get_widget('label_tasks').set_text("Datei %s/%s dekodieren" % (count + 1, len(file_conclusions)))
                   
            curr_dir = ""      
            if os.name == "posix":
                command = "%s -i %s -e %s -p %s -o %s" % (self.config.get('decode', 'path'), file_conclusion.otrkey, email, password, self.config.get('folders', 'new_otrkeys'))
            
                if self.config.get('decode', 'correct') == 0:
                    command += " -q"
            else: # windows
         
               # TODO: de-hack, use subprocess module and get rid of while events_pending()...
               curr_dir = os.getcwd()   
               os.chdir(dirname(self.config.get('decode', 'path')))

               command = '%s -uotr %s -pwotr %s -f %s -c true -hide' % (basename(self.config.get('decode', 'path')), email, password, file_conclusion.otrkey)               
               # Multidecoder.exe -uotr belbers@gmx.net -pwotr hasihas -f X:\Die_Simpsons.otrkey -c true -hide

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
                file_conclusion.uncut_avi = file_conclusion.otrkey[0:len(file_conclusion.otrkey)-7]  
                                  
                # TODO: Verschieben auf nach dem zeigen der zusammenfassung?            
                # move to trash
                target = self.config.get('folders', 'trash')
                fileoperations.move_file(file_conclusion.otrkey, target)
            else:            
                file_conclusion.decode.status = Status.ERROR
                file_conclusion.decode.message = error_message
                
        return True
            
    def cut(self, file_conclusions, action, rename_by_schema):                      
        if self.config.get('cut', 'avidemux') == "":
            self.__gui.message_error_box("Es ist kein Avidemux angegeben!")
            return False        

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
            cut_action = None
            cutlists = []
            
            if self.config.get('cut', 'cut_action') == Cut_action.MANUALLY:
                cut_action = Cut_action.MANUALLY

            elif self.config.get('cut', 'cut_action') == Cut_action.BEST_CUTLIST:                
                cut_action = Cut_action.BEST_CUTLIST

                def error_cb(error):
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = error

                cutlists = cutlists_management.download_cutlists(file_conclusion.uncut_avi, self.config.get('cut', 'server'), error_cb)                           
                
                if len(cutlists) == 0:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = "Keine Cutlists gefunden!"          
                    continue
            
            elif self.config.get('cut', 'cut_action') == Cut_action.LOCAL_CUTLIST:
                cut_action = Cut_action.LOCAL_CUTLIST
                 
            else:            
                # show dialog
                self.__gui.dialog_cut.filename = file_conclusion.uncut_avi
                self.__gui.dialog_cut.get_widget('label_file').set_markup("<b>%s</b>" % basename(file_conclusion.uncut_avi))
                self.__gui.dialog_cut.get_widget('label_warning').set_markup('<span size="small">Wichtig! Die Datei muss im Ordner "%s" und unter einem neuen Namen gespeichert werden, damit das Programm erkennt, dass diese Datei geschnitten wurde!</span>' % self.config.get('folders', 'new_otrkeys'))

                if self.config.get('cut', 'cut_action') == Cut_action.ASK:
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
               
                GeneratorTask(cutlists_management.download_cutlists, cutlist_found_cb, completed).start(file_conclusion.uncut_avi, self.config.get('cut', 'server'), error_cb)
                
                response = self.__gui.dialog_cut.run()                
                self.__gui.dialog_cut.hide()
                
                if response < 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen"
                    continue
                else:
                    cut_action = response
                    
            # save cut_action
            file_conclusion.cut.cut_action = cut_action

            if cut_action == Cut_action.BEST_CUTLIST:
                if len(cutlists) == 0:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Keine Cutlist gefunden"
                    continue
            
                best_cutlist = cutlists_management.get_best_cutlist(cutlists)                 
                
                cut_avi, local_cutlist, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, best_cutlist, rename_by_schema)

                if cut_avi == None:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error    
                else:
                    file_conclusion.cut.status = Status.OK
                    file_conclusion.cut_avi = cut_avi
                    file_conclusion.cut.local_cutlist = local_cutlist
                    file_conclusion.cut.cutlist = best_cutlist                            
                
            elif cut_action == Cut_action.CHOOSE_CUTLIST:
                cut_avi, local_cutlist, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, self.__gui.dialog_cut.chosen_cutlist, rename_by_schema)
                
                if cut_avi == None:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error    
                else:
                    file_conclusion.cut.status = Status.OK
                    file_conclusion.cut_avi = cut_avi
                    file_conclusion.cut.local_cutlist = local_cutlist
                    file_conclusion.cut.cutlist = self.__gui.dialog_cut.chosen_cutlist

            elif cut_action == Cut_action.LOCAL_CUTLIST:
                filename_cutlist = file_conclusion.uncut_avi + ".cutlist"
                
                if not exists(filename_cutlist):
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = "Keine lokale Cutlist gefunden"
                    continue
               
                cut_avi, local_cutlist, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, filename_cutlist, rename_by_schema, local=True)
                
                if cut_avi == None:
                    file_conclusion.cut.status = Status.ERROR
                    file_conclusion.cut.message = error
                else:
                    file_conclusion.cut.status = Status.OK
                    file_conclusion.cut_avi = cut_avi
                    file_conclusion.cut.local_cutlist = local_cutlist

            elif cut_action == Cut_action.MANUALLY: # MANUALLY
                command = "%s --load %s >>/dev/null" % (self.config.get('cut', 'avidemux'), file_conclusion.uncut_avi)
                avidemux = subprocess.Popen(command, shell=True)    
                while avidemux.poll() == None:
                    # wait
                    pass
                    
                file_conclusion.cut.status = Status.OK
              
        # after iterating over all items:
        return True
             
    def cut_file_by_cutlist(self, filename, cutlist, rename_by_schema, local=False):
              
        if local:
            local_filename = cutlist            
        else:                             
            local_filename = filename + ".cutlist"
       
        # download cutlists     
        try:
            cutlists_management.download_cutlist(cutlist, self.config.get('cut', 'server'), local_filename)
        except IOError:
            return None, None, "Verbindungsprobleme"  
              
        # get dictionary of cuts
        cuts = cutlists_management.get_cuts_of_cutlist(local_filename)
        
        if type(cuts) != list: # error occured
            return None, None, "Fehler: cuts!=list (%s)" % cuts
                  
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

        # generate filename for a cut avi
        if self.config.get('rename', 'rename_cut'):
            directory = dirname(filename)
            name = basename(filename)        
            new_name = rename_by_schema(name)
                    
            cut_avi = join(directory, new_name)        
        else:
            cut_avi = filename[0:len(filename)-4] # remove .avi
            cut_avi += "-cut.avi"
           
                   
        f.writelines([
            '//** Postproc **\n',
            'app.video.setPostProc(3,3,0);\n',
            'app.video.setFps1000(25000);\n',
            '\n',
            '//** Video Codec conf **\n',
            'app.video.codec("Copy","CQ=4","0");\n',
            '\n',
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
        command = "%s --force-smart --run tmp.js --quit >>/dev/null" % self.config.get('cut', 'avidemux') # --nogui
        avidemux = subprocess.Popen(command, shell=True)
        while avidemux.poll()==None:
            while events_pending():
                main_iteration(False)  
        
        fileoperations.remove_file('tmp.js')
        
        # successful
        return cut_avi, local_filename, None
