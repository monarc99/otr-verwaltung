#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import sys
from os import listdir, walk, mkdir
from os.path import join, isdir, basename, dirname
import re
import base64
import time
import pango
import popen2
import subprocess
import gobject
import urllib
import xml.dom.minidom
import ConfigParser

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
    import pango
except:
    sys.exit(-1)
    
# intern
import gui
from configparser import Config
import fileoperations
from filesconclusion import FileConclusion
from constants import Section, Action, Cut_action, Save_Email_Password, Status

class App:
    
    def __init__(self):             
        # read configs
        self.config = Config(join(sys.path[0], ".otr-conf"))

        self.__search_text = ""
        self.blocked = False
        # tuple: action, len of files
        self.__block_action = None
        # tuple: number of file, progress
        self.__decode_progress = -1, 0
        # number of file
        self.__cut_count = -1
    
        # load gui
        self.__gui = gui.GUI(self, join(sys.path[0], "otr.ui"))       
        
        # show undecoded otrkeys         
        self.show_section(Section.OTRKEY)
        
        # regex
        self.__uncut_video = re.compile('.*_([0-9]{2}\.){2}([0-9]){2}_([0-9]){2}-([0-9]){2}_.*_([0-9])*_TVOON_DE.mpg\.(avi|HQ\.avi|mp4)$')
        self.__cut_video = re.compile('.*(avi|mp4)$')     
        
    ### 
    ### Show sections
    ###
    
    def show_section(self, section):
        """ Shows one of the five different sections. 
            - set files of treeview
            - set section-variable to current section
            - set appropriate toolbar"""

        # set current section
        self.section = section
        
        # set toolbar
        self.__gui.set_toolbar(section)
                
        self.__gui.main_window['treeviewFiles_store'].clear()
        files = []
        text = ""
        
        if section==Section.OTRKEY:            
            text, files = self.section_otrkey()   
        
        elif section==Section.AVI_UNCUT:
            text, files = self.section_avi_uncut()   
    
        elif section==Section.AVI_CUT:
            text, files = self.section_avi_cut()   
            
        elif section==Section.TRASH:
            text, files = self.section_trash()   

        elif section==Section.ARCHIVE: 
            # returns NO files       
            text = self.section_archive()
            self.__gui.main_window['treeviewFiles'].expand_all()

        if len(files)>0: # this is not executed, when the section is "Archive"
            if len(files)==1:
                text += " (1 Datei)"
            else:
                text += " (%s Dateien) " % len(files)
            
            files.sort()
            # put filenames into treestore
            for f in files:
                self.append_row_treeview_files(None, f)

        # set message textfilenames_action_status[file][action][0]
        self.__gui.main_window['labelMessage'].set_text(text)
             
    # helper for different section
    def section_otrkey(self):
        text = "Diese Dateien wurden noch nicht dekodiert." 
        path = self.config.get('folders', 'new_otrkeys')
        
        if path == "":      
            return text, []
        
        files = [join(path, f) for f in listdir(path) if f.endswith(".otrkey") and self.search(f)]                           
            
        return (text, files)
         
    def section_avi_uncut(self):
        text = "Diese Dateien wurden noch nicht geschnitten."
        path = self.config.get('folders', 'new_otrkeys')
        
        files = [join(path, f) for f in listdir(path) if self.__uncut_video.match(f) and self.search(f)]
            
        return (text, files)
        
    def section_avi_cut(self):
        text = "Diese avi-Dateien sind fertig geschnitten."
        if self.config.get('common', 'use_archive'):
            text += " Sie können ins Archiv verschoben werden."
                
        path = self.config.get('folders', 'new_otrkeys')
        
        files = []                
        for f in listdir(path):
            if not self.__uncut_video.match(f):
                if self.__cut_video.match(f):
                    if self.search(f):
                        files += [join(path, f)]
        
        return (text, files)
        
    def section_trash(self):
        text = "Diese otrkey- und avi-Dateien wurden bereits dekodiert bzw. geschnitten. Sie können normalerweise gelöscht werden."
        path = self.config.get('folders', 'trash')
                    
        files = [join(path, f) for f in listdir(path) if (f.endswith('.otrkey') or f.endswith('.avi')) and self.search(f)]
                
        return (text, files)

    def section_archive(self):
        text = "Diese Dateien wurden ins Archiv verschoben."

        path = self.config.get('folders', 'archive')
               
        self.tree(None, path)
        
        return text            
                 
    # recursive function for archive to add folders and files with a tree structure
    def tree(self, parent, path=None):              
        if parent != None:            
            dir = self.__gui.get_filename(parent)
        else:  # base path (archive directory)
            dir = path

        files = []
        files = listdir(dir)            

        for file in files:
            full_path = join(dir, file)
            
            if isdir(full_path):                
                iter = self.append_row_treeview_files(parent, full_path)
                self.tree(iter)
            else:
                if file.endswith('.avi'):
                    if self.search(file):
                        self.append_row_treeview_files(parent, full_path)

    ###
    ### Helpers
    ###

    def status_to_s(self, status):
        if status==Status.OK:
            return "OK"
        elif status==Status.ERROR:
            return "Fehler"
        elif status==Status.NOT_DONE:
            return "Nicht durchgeführt"
            
    def action_to_s(self, action):              
        if action==Action.DECODE:
            return "Dekodieren"
        elif action==Action.CUT:
            return "Schneiden"
     
    def append_row_treeview_files(self, parent, filename):        
        iter = self.__gui.append_row_treeviewFiles(parent, filename, fileoperations.get_size(filename), fileoperations.get_date(filename))
        return iter
     
    ### 
    ### Search
    ### 
                      
    def start_search(self, search):
        self.__search_text = search.lower()
        
        # create dict of counts
        counts = {}

        for method, section in [(self.section_otrkey, Section.OTRKEY),
                                (self.section_avi_uncut, Section.AVI_UNCUT),
                                (self.section_avi_cut, Section.AVI_CUT),
                                (self.section_trash, Section.TRASH)]:
            files = []
            text, files = method()   
            count = len(files)
            if count > 0:
                counts[section] = "(%s)" % count
            else:
                counts[section] = ""
         
        # archive
        files = []
        for root, dirs, wfiles in walk(self.config.get('folders', 'archive')):
            for f in wfiles:
                if f.endswith('.avi') and self.search(f):
                    files += [join(root, f)]

        count = len(files)
        if count > 0:
            counts[Section.ARCHIVE] = "(%s)" % count
        else:
            counts[Section.ARCHIVE] = ""
        
        self.show_section(self.section)                   
        return counts
    
    def stop_search(self):
        self.__search_text = ""
        self.show_section(self.section)
        
    def search(self, f):
        if self.__search_text == "":
            return True
        else:    
            if self.__search_text in f.lower():
                return True
            else:
                return False
        
    ###
    ### Actions
    ###        
    
    def perform_action(self, action, filenames):
        """ Performs an action (toolbar, context menu, etc.) """
        
        if len(filenames) == 0 and action!=Action.NEW_FOLDER:        
            self.__gui.message_box("Es sind keine Dateien markiert!", gtk.MESSAGE_INFO, gtk.BUTTONS_OK)   
            return
        
        # different actions:
        if action==Action.DECODE or action==Action.CUT or action==Action.DECODEANDCUT:
                                        
            # create file_conclusions array        
            file_conclusions = []
                
            if action==Action.DECODE or action==Action.DECODEANDCUT:
                for otrkey in filenames:
                    file_conclusions.append(FileConclusion(action, otrkey=otrkey))
                
            if action==Action.CUT:
                for uncut_avi in filenames:
                    file_conclusions.append(FileConclusion(action, uncut_avi=uncut_avi))
              
            self.__block_action = action, len(file_conclusions)
                
            # decode files                    
            if action==Action.DECODE or action==Action.DECODEANDCUT:
                if self.action_decode(file_conclusions)==False: 
                    return
            
            self.__decode_progress = -1, 0
            
            # cut files
            if action==Action.CUT or action==Action.DECODEANDCUT:
                if self.action_cut(file_conclusions, action)==False:
                    return                    

            self.__cut_count = -1
                
            # show conclusion
            dialog = self.__gui.build_conclusion_dialog(file_conclusions, action)
            dialog.run()         
            
            file_conclusions = self.__gui.file_conclusions
            
            if action != Action.DECODE:
                count = 0
                for file_conclusion in file_conclusions:                    
                    if file_conclusion.cut.rating > -1:
                        url = self.config.get('cut', 'server') + "rate.php?version=0.9.8.0&rate=%s&rating=%s" % (file_conclusion.cut.cutlist, file_conclusion.cut.rating)

                        try:
                            urllib.urlopen(url)                                 
                            count += 1
                        except IOError, e:
                            print e
                
                if count == 1:
                    self.__gui.message_box("Es wurde 1 Cutlisten bewertet!", gtk.MESSAGE_INFO, gtk.BUTTONS_OK)
                elif count > 1:
                    self.__gui.message_box("Es wurden %s Cutlisten bewertet!" % count, gtk.MESSAGE_INFO, gtk.BUTTONS_OK)

            # update section
            self.blocked = False
            self.__gui.windows['main_window'].show()
            self.show_section(self.section)        
            
        elif action==Action.DELETE:
            self.action_delete(filenames)
            self.show_section(self.section)        
            
        elif action==Action.ARCHIVE:
            self.action_archive(filenames)
            self.show_section(self.section)        
                                
        elif action==Action.PLAY:                    
            self.action_play(filenames[0])        
            
        elif action==Action.RESTORE:
            self.action_restore(filenames)
            self.show_section(self.section)
        
        elif action==Action.RENAME:
            self.action_rename(filenames)
            self.show_section(self.section)
        
        elif action==Action.NEW_FOLDER:
            if len(filenames) == 0:
                self.action_new_folder(self.config.get('folders', 'archive'))
            else:
                self.action_new_folder(filenames[0])
            self.show_section(self.section)
        
        elif action==Action.CUT_PLAY:
            self.action_cut_play(filenames[0])
            
        elif action==Action.REAL_DELETE:
            self.action_real_delete(filenames)
            self.show_section(self.section)
      
    def get_notify_text(self):
        decode_count, progress = self.__decode_progress
        cut_count = self.__cut_count
        action, length = self.__block_action
      
        text = ""
        if action==Action.DECODE or action==Action.DECODEANDCUT:
            if decode_count > -1:
                text += "Datei %i/%i wird dekodiert: %i%% \n" % (decode_count + 1, length, progress)
            else:
                text += "Dekodieren abgeschlossen.\n"
                
        if action==Action.CUT or (action==Action.DECODEANDCUT and decode_count == -1):
            if cut_count > -1:
                text += "Datei %i/%i wird geschnitten." % (cut_count + 1, length)
            else:
                text += "Schneiden abgeschlossen."
          
        return text
      
    # helpers for actions                   
    def action_decode(self, file_conclusions):           
        
        # no decoder        
        if not "decode" in self.config.get('decode', 'path'): # no decoder specified
            # dialog box: no decoder
            self.__gui.message_box("Es ist kein korrekter Dekoder angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)   
            return False
        
        # retrieve email and password
        # user did not save email and password
        if self.config.get('decode', 'save_email_password') == Save_Email_Password.DONT_SAVE:
            # let the user type in his data through a dialog
            response = self.__gui.windows['dialog_email_password'].run()
            self.__gui.windows['dialog_email_password'].hide() 
            
            if response==gtk.RESPONSE_OK:
                email = self.__gui.dialog_email_password['entryDialogEMail'].get_text()
                password = self.__gui.dialog_email_password['entryDialogPassword'].get_text()                               
            else: # user pressed cancel
                return False
                         
        else: # user typed email and password in         
            email = self.config.get('decode', 'email')
            password = base64.b64decode(self.config.get('decode', 'password')) 
        
        # start decoding, block app
        # now this method may not return "False"
        self.__gui.windows['main_window'].hide()
        self.blocked = True
        self.__gui.notify_popup("OTR-Verwaltung führt die gewählten Aktionen aus...", "", 3)
                   
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
            # update progress
            self.__decode_progress = count, 0
                   
            command = "%s -i %s -e %s -p %s -o %s" % (self.config.get('decode', 'path'), file_conclusion.otrkey, email, password, self.config.get('folders', 'new_otrkeys'))
            # TODO: Reset
            print command
         #   if self.config.get('decode', 'correct') == 0:
         #       command += " -q"
                                   
            (pout, pin, perr) = popen2.popen3(command)
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
                    self.__decode_progress = count, progress
                    while gtk.events_pending():
                        gtk.main_iteration(False)
                except ValueError:                
                    pass
            
            # errors?
            errors = perr.readlines()
            error_message = ""
            for error in errors:
                error_message += error.strip()
                            
            # close process
            pout.close()
            perr.close()
            pin.close()
                                                            
            if len(errors)==0: # dekodieren erfolgreich                
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

    def action_cut(self, file_conclusions, action):               
        # start cutting, block app
        # now this method may not return "False"
        self.__gui.windows['main_window'].hide()
        self.blocked = True
        self.__gui.notify_popup("OTR-Verwaltung führt die gewählten Aktionen aus...", "", 3)
        
        for count, file_conclusion in enumerate(file_conclusions):
            self.__cut_count = count
    
            # file correctly decoded?            
            if action==Action.DECODEANDCUT:
                if file_conclusion.decode.status == Status.ERROR:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Datei wurde nicht dekodiert."
                    continue

            # how should the file be cut?
            cut_action = None
            if self.config.get('cut', 'cut_action') == Cut_action.ASK:
            
                self.__gui.dialog_cut['labelCutFile'].set_text(basename(file_conclusion.uncut_avi))
                self.__gui.dialog_cut['labelWarning'].set_text('Wichtig! Die Datei muss im Ordner "%s" und unter einem neuen Namen gespeichert werden, damit das Programm erkennt, dass diese Datei geschnitten wurde!' % self.config.get('folders', 'new_otrkeys'))

                response = self.__gui.windows['dialog_cut'].run()
                self.__gui.windows['dialog_cut'].hide()
                
                if response == gtk.RESPONSE_OK:            
                    if self.__gui.dialog_cut['radioCutBestCutlist'].get_active() == True:
                        cut_action = Cut_action.BEST_CUTLIST
                    elif self.__gui.dialog_cut['radioCutChooseCutlist'].get_active() == True:
                        cut_action = Cut_action.CHOOSE_CUTLIST
                    else:                    
                        cut_action = Cut_action.MANUALLY
                else:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen"
                    continue
            
            else: # !=ASK
                cut_action = self.config.get('cut', 'cut_action')
 
            # save cut_action
            file_conclusion.cut.cut_action = cut_action

            if cut_action == Cut_action.BEST_CUTLIST:
                # download all cutlist for the files and choose
                # the cutlist with the best rating
                
                dom_cutlists, error_message = self.get_dom_from_cutlist(file_conclusion.uncut_avi)
                
                if dom_cutlists==None:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = error_message
                else:                   
                    cutlists = {}             
                    for cutlist in dom_cutlists.getElementsByTagName('cutlist'):                          
                        ratingbyauthor = self.read_value(cutlist, "ratingbyauthor")
                        userrating = self.read_value(cutlist, "rating")
                                                
                        if ratingbyauthor=="":
                            rating = userrating
                        elif userrating=="":
                            rating = ratingbyauthor
                        else:
                            rating = float(ratingbyauthor) * 0.3 + float(userrating) * 0.7
    
                        cutlists[int(self.read_value(cutlist, "id"))] = rating
                    
                    if len(cutlists)==0:
                        file_conclusion.cut.status = Status.NOT_DONE
                        file_conclusion.cut.message = "Keine Cutlist gefunden."
                    else:                
                        sort_cutlists = cutlists.items()
                        sort_cutlists.sort(key=lambda x: x[1], reverse=True) # first is the best
                                        
                        best_cutlist = sort_cutlists[0][0] # get first (=the best) cutlist; from the tuple, get the first (id) item
                        
                        cut_avi, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, best_cutlist)
                        if cut_avi == None:
                            file_conclusion.cut.status = Status.ERROR
                            file_conclusion.cut.message = error    
                        else:
                            file_conclusion.cut.status = Status.OK
                            file_conclusion.cut_avi = cut_avi
                            file_conclusion.cut.cutlist = best_cutlist                            
                
            elif cut_action == Cut_action.CHOOSE_CUTLIST:
                # download all cutlist and display them to
                # the user

                self.__gui.dialog_cutlist['treeviewCutlists_store'].clear()                
                dom_cutlists, error_message = self.get_dom_from_cutlist(file_conclusion.uncut_avi)
                
                cutlists_found = False
                 
                if dom_cutlists==None:
                    self.__gui.message_box(error_message, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = error_message
                else:                   
                    for cutlist in dom_cutlists.getElementsByTagName('cutlist'):
                        cutlists_found = True
                                                                 
                        data_array = [
                            self.read_value(cutlist, "id"),
                            self.read_value(cutlist, "author"),
                            self.read_value(cutlist, "ratingbyauthor"),
                            self.read_value(cutlist, "rating"),
                            self.read_value(cutlist, "ratingcount"),
                            self.read_value(cutlist, "cuts"),
                            self.read_value(cutlist, "actualcontent"),
                            self.read_value(cutlist, "usercomment"),
                            self.read_value(cutlist, "filename"),
                            self.read_value(cutlist, "withframes"),
                            self.read_value(cutlist, "withtime"),
                            self.read_value(cutlist, "duration")]
                    
                        self.__gui.add_cutlist(data_array)
                
                    if cutlists_found:                        
                        self.__gui.dialog_cutlist['labelCutlistFile'].set_text(basename(file_conclusion.uncut_avi))
                        response = self.__gui.windows['dialog_cutlist'].run()
                        self.__gui.windows['dialog_cutlist'].hide()
                        
                        treeselection = self.__gui.dialog_cutlist['treeviewCutlists'].get_selection()  
                        
                        if treeselection.count_selected_rows()==0 or response != gtk.RESPONSE_OK:                            
                            file_conclusion.cut.status = Status.NOT_DONE
                            file_conclusion.cut.message = "Keine Cutlist gewählt."
                        else:
                            # retrieve id of chosen cutlist
                            (model, iter) = treeselection.get_selected()                   
                            chosen_cutlist = model.get_value(iter, 0)
                            
                            cut_avi, error = self.cut_file_by_cutlist(file_conclusion.uncut_avi, chosen_cutlist)
                            
                            if cut_avi == None:
                                file_conclusion.cut.status = Status.ERROR
                                file_conclusion.cut.message = error    
                            else:
                                file_conclusion.cut.status = Status.OK
                                file_conclusion.cut_avi = cut_avi
                                file_conclusion.cut.cutlist = chosen_cutlist         
                                                                                        
                    else: # no cutlist in xml
                        file_conclusion.cut.status = Status.NOT_DONE
                        file_conclusion.cut.message = "Keine Cutlist gefunden."

            elif cut_action == Cut_action.MANUALLY: # MANUALLY
                command = "%s --load %s >>/dev/null" %(self.config.get('cut', 'avidemux'), file_conclusion.uncut_avi)
                avidemux = subprocess.Popen(command, shell=True)    
                while avidemux.poll()==None:
                    # wait
                    pass
                    
                file_conclusion.cut.status = Status.OK
                    
            if file_conclusion.cut.status == Status.OK:
                # TODO: Verschieben auf nach dem zeigen der zusammenfassung?            
                # action after cut
                # move to trash
                target = self.config.get('folders', 'trash')
                fileoperations.move_file(file_conclusion.uncut_avi, target)
             
            # update progress
            self.__cut_count = count
        
        # after iterating over all items:
        return True
       
    def get_dom_from_cutlist(self, avi):
        size = fileoperations.get_size(avi)
        url = self.config.get('cut', 'server') + "getxml.php?version=0.9.8.0&ofsb=" + str(size)

        try:
            handle = urllib.urlopen(url)     
        except IOError:
            return None, "Verbindungsprobleme"
                       
        try:
            dom_cutlists = xml.dom.minidom.parse(handle)
            handle.close()
            
            return dom_cutlists, None
        except:
            return None, "Keine Cutlist gefunden"
        
    def read_value(self, cutlist_element, node_name):
        value=None
        try:
            elements = cutlist_element.getElementsByTagName(node_name)
            for node in elements[0].childNodes:
                return node.nodeValue
        except:
            return ""
        
        if value==None:
            return ""
             
    def cut_file_by_cutlist(self, filename, cutlist):
        # download cutlist
        url = self.config.get('cut', 'server') + "getfile.php?id=" + str(cutlist)
        
        # save cutlist to folder
        local_filename = join(self.config.get('folders', 'new_otrkeys'), basename(filename) + ".cutlist")
        
        try:
            local_filename, headers = urllib.urlretrieve(url, local_filename)
        except IOError:
            return None, "Verbindungsprobleme"
        
        config_parser = ConfigParser.ConfigParser()        
        config_parser.read(local_filename)
       
        noofcuts = 0        
        cuts = {}
        try:
            noofcuts = int(config_parser.get("General", "NoOfCuts"))
           
            for count in range(noofcuts):
                cuts[count] = (
                    float(config_parser.get("Cut"+str(count), "Start")), 
                    float(config_parser.get("Cut"+str(count), "Duration")))            
            
        except ConfigParser.NoSectionError, (ErrorNumber, ErrorMessage):
            return None, "Fehler in Cutlist: " + ErrorMessage
        except ConfigParser.NoOptionError, (ErrorNumber, ErrorMessage):
            return None, "Fehler in Cutlist: " + ErrorMessage
        
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
            
        for count, (start, duration) in cuts.iteritems():
            frame_start = start * 25   
            frame_duration = duration * 25
            f.write("app.addSegment(0, %s, %s);\n" %(str(int(frame_start)), str(int(frame_duration))))

        # generate filename for a cut avi
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
        command = "avidemux --force-smart --run tmp.js --quit >>/dev/null" # --nogui
        avidemux = subprocess.Popen(command, shell=True)
        while avidemux.poll()==None:
            while gtk.events_pending():
                gtk.main_iteration(False)  
        
        fileoperations.remove('tmp.js')
        
        # successful
        return cut_avi, None
                        
    def action_play(self, filename):
        player = self.config('play', 'player')

        if not self.__cut_video.match(filename):
            self.__gui.message_box("Die ausgewählte Datei ist kein Video!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return 
            
        if player=='':
            self.__gui.message_box("Es ist kein Player angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        p = subprocess.Popen([player, filename])
    
    def action_cut_play(self, filename):
        mplayer = self.config('play', 'mplayer')
        
        if not self.__uncut_video.match(filename):
            self.__gui.message_box("Die ausgewählte Datei ist kein ungeschnittenes Video!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return 
            
        if mplayer=='':
            self.__gui.message_box("Der MPlayer ist nicht angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        # get best cutlist
        dom_cutlists, error_message = self.get_dom_from_cutlist(filename)
        
        best_cutlist = None
        
        if dom_cutlists==None:
            self.__gui.message_box(error_message, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        else:                   
            cutlists = {}             
            for cutlist in dom_cutlists.getElementsByTagName('cutlist'):                          
                ratingbyauthor = self.read_value(cutlist, "ratingbyauthor")
                userrating = self.read_value(cutlist, "rating")
                                        
                if ratingbyauthor=="":
                    rating = userrating
                elif userrating=="":
                    rating = ratingbyauthor
                else:
                    rating = float(ratingbyauthor) * 0.3 + float(userrating) * 0.7

                cutlists[int(self.read_value(cutlist, "id"))] = rating
            
            if len(cutlists)==0:
                self.__gui.message_box("Keine Cutlist gefunden!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
                return
            else: 
                sort_cutlists = cutlists.items()
                sort_cutlists.sort(key=lambda x: x[1], reverse=True) # first is the best
                       
                best_cutlist = sort_cutlists[0][0] # get first (=the best) cutlist; from the tuple, get the first (id) item
                
        # download cutlist + save it
        url =self.config.get('cut', 'server') + "getfile.php?id=" + str(best_cutlist)        
        local_filename = join(self.config.get('folders', 'new_otrkeys'), basename(filename) + ".cutlist")
        
        try:
            local_filename, headers = urllib.urlretrieve(url, local_filename)
        except IOError:
            self.__gui.message_box("Verbindungsprobleme", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        config_parser = ConfigParser.ConfigParser()        
        config_parser.read(local_filename)
       
        print local_filename
       
        noofcuts = 0        
        cuts = []
        try:
            noofcuts = int(config_parser.get("General", "NoOfCuts"))
           
            for count in range(noofcuts):
                cuts.append((float(config_parser.get("Cut"+str(count), "Start")), float(config_parser.get("Cut"+str(count), "Duration"))))
            
        except ConfigParser.NoSectionError, (ErrorNumber, ErrorMessage):
            self.__gui.message_box("Fehler in Cutlist: " + ErrorMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        except ConfigParser.NoOptionError, (ErrorNumber, ErrorMessage):
            self.__gui.message_box("Fehler in Cutlist: " + ErrorMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        # make edl
        # http://www.mplayerhq.hu/DOCS/HTML/en/edl.html
        # [Begin Second] [End Second] [0=Skip/1=Mute]
        f = open(".tmp.edl", "w")
        
        f.write("0 %s 0\n" % (cuts[0][0] - 1))

        for count, (start, duration) in enumerate(cuts):
            end = start + duration
            if count+1 == len(cuts):
                f.write("%s 50000 0\n" % (end))
            else:
                f.write("%s %s 0\n" % (end, (cuts[count+1][0] - 1)))
        
        p = subprocess.Popen([mplayer, "-edl", ".tmp.edl", filename])
       
    def action_archive(self, filenames):       
        # widgets
        dialog = self.__gui.windows['dialog_archive']
        treeview_files = self.__gui.dialog_archive['treeviewFilesRename']
        treestore_files = self.__gui.dialog_archive['treeviewFilesRename_store']
        treeview_folders = self.__gui.dialog_archive['treeviewFolders']
        treestore_folders = self.__gui.dialog_archive['treeviewFolders_store']
                
        self.__gui.dialog_archive['labelFiles'].set_text("%s Datei(en) zum Archivieren ausgewählt." % len(filenames))
        
        # fill rename tree
        dict_files_iter = {}        
        for f in filenames:
            iter = self.__gui.append_row_treeviewFilesRename(basename(f))
            # keep relation between filename and iter
            dict_files_iter[f] = iter
            
        # fill tree of folders  
        root = self.__gui.append_row_treeviewFolders(None, self.config.get('folders', 'archive'))    
        self.tree_folders(root)        
        # select first node
        selection = treeview_folders.get_selection()
        selection.select_path(0)
        
        # expand
        treeview_folders.expand_all()
        
        result = dialog.run()

        if result==gtk.RESPONSE_OK:            
            # get selection
            selection = treeview_folders.get_selection()
            (model, iter) = selection.get_selected()
            
            # get target path
            target_folder = model.get_value(iter, 0)
            
            for f in filenames:
                # get new filename
                new_name = treestore_files.get_value(dict_files_iter[f], 0)
            
                if not new_name.endswith('.avi'):
                    new_name += '.avi'
            
                fileoperations.move_file(f, target_folder)   
                    
        dialog.hide()
                
        # clear treeview and listview
        treestore_folders.clear()
        treestore_files.clear()

    # recursive
    def tree_folders(self, parent):              
        dir = self.__gui.dialog_archive['treeviewFolders_store'].get_value(parent, 0)
            
        files = []
        files = listdir(dir)            

        for file in files:
            full_path = join(dir, file)
            
            if isdir(full_path):                
                iter = self.__gui.append_row_treeviewFolders(parent, full_path)
                self.tree_folders(iter)

       
    def action_delete(self, filenames):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.__gui.question_box(message + "in den Müll verschoben werden?"):
            for f in filenames:
                target = self.config.get('folders', 'trash')
                fileoperations.move_file(f, target)
                
    def action_real_delete(self, filenames):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.__gui.question_box(message + "endgültig gelöscht werden?"):
            for f in filenames:
                fileoperations.remove(f)
    
    def action_restore(self, filenames):
        for f in filenames:
            fileoperations.move_file(f, self.config.get('folders', 'new_otrkeys'))
    
    def action_rename(self, filenames):
        dialog = self.__gui.windows['dialog_rename']
        vbox = self.__gui.dialog_rename['vboxRename']
        
        entries = {}
        for f in filenames:
            entries[f] = gtk.Entry()
            entries[f].set_text(basename(f))
            entries[f].show()
            vbox.pack_start(entries[f])
        
        dialog.set_title("Umbenennen")    
        if dialog.run() == gtk.RESPONSE_OK:            
            for f in filenames:
                new_name = join(dirname(f), entries[f].get_text())
                
                if f.endswith('.avi') and not new_name.endswith('.avi'):
                    new_name+='.avi'
                    
                fileoperations.rename(f, new_name)
        
        dialog.hide()
            
        # remove entry widgets
        for f in entries:
            vbox.remove(entries[f])
                               
    def action_new_folder(self, filename):
        if isdir(filename):
            dirname = filename
        else:
            dirname = dirname(filename)

        dialog = self.__gui.windows['dialog_rename']
        vbox = self.__gui.dialog_rename['vboxRename']

        entry = gtk.Entry()
        entry.show()
        vbox.pack_start(entry)
        dialog.set_title("Neuer Ordner")
        
        if dialog.run()==gtk.RESPONSE_OK and entry.get_text!="":            
            mkdir(join(dirname, entry.get_text()))
            
        dialog.hide()
        
        vbox.remove(entry)
        
    def main(self):
        self.__gui.run()
        
        self.config.save()
        

app = App()
app.main()
