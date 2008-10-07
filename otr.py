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


# TODO: remove this from otr.py. this dependency belongs to gui
# TODO: do i need pygtk? (see also other files)
try:
    from gtk import events_pending, main_iteration, RESPONSE_OK
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)


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

# intern
import otrpath
from gui.gui import Gui
from configparser import Config
import fileoperations
from filesconclusion import FileConclusion
from constants import Section, Action, Cut_action, Save_Email_Password, Status

class App:
    
    def __init__(self):             
        # read configs
        self.config = Config(otrpath.get_path(".otr-conf"))

        self.__search_text = ""
        self.blocked = False
        # tuple: action, len of files
        self.__block_action = None
        # tuple: number of file, progress
        self.__decode_progress = -1, 0
        # number of file
        self.__cut_count = -1
    
        # load gui
        self.__gui = Gui(self)
    
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
        self.__gui.main_window.set_toolbar(section)
                
        self.__gui.main_window.clear_files()
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
        self.__gui.main_window.get_widget('labelMessage').set_text(text)
             
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
            dir = self.__gui.main_window.get_filename(parent)
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
     
    def append_row_treeview_files(self, parent, filename):        
        iter = self.__gui.main_window.append_row_files(parent, filename, fileoperations.get_size(filename), fileoperations.get_date(filename))
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
            self.__gui.message_info_box("Es sind keine Dateien markiert!")
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
            dialog = self.__gui.dialog_conclusion.build(file_conclusions, action)
            dialog.run()         
            
            file_conclusions = self.__gui.dialog_conclusion.file_conclusions
            
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
                    self.__gui.message_info_box("Es wurde 1 Cutlisten bewertet!")
                elif count > 1:
                    self.__gui.message_info_box("Es wurden %s Cutlisten bewertet!" % count)

            # update section
            self.blocked = False
            self.__gui.main_window.show()
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
        
        # start decoding, block app
        # now this method may not return "False"
        self.__gui.main_window.hide()
        self.blocked = True
        self.__gui.notify.popup("OTR-Verwaltung führt die gewählten Aktionen aus...", "", 3)
                   
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
            # update progress
            self.__decode_progress = count, 0
                   
            command = "%s -i %s -e %s -p %s -o %s" % (self.config.get('decode', 'path'), file_conclusion.otrkey, email, password, self.config.get('folders', 'new_otrkeys'))
            
            if self.config.get('decode', 'correct') == 0:
                command += " -q"
                                   
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
                    while events_pending():
                        main_iteration(False)
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
        self.__gui.main_window.hide()
        self.blocked = True
        # only show when everything is donw automatically, otherwise it's confusing
        if self.config.get('cut', 'cut_action') == Cut_action.BEST_CUTLIST: 
            self.__gui.notify.popup("OTR-Verwaltung führt die gewählten Aktionen aus...", "", 3)
        
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
            
                self.__gui.dialog_cut.get_widget('labelCutFile').set_text(basename(file_conclusion.uncut_avi))
                self.__gui.dialog_cut.get_widget('labelWarning').set_text('Wichtig! Die Datei muss im Ordner "%s" und unter einem neuen Namen gespeichert werden, damit das Programm erkennt, dass diese Datei geschnitten wurde!' % self.config.get('folders', 'new_otrkeys'))

                response = self.__gui.dialog_cut.run()
                self.__gui.dialog_cut.hide()
                
                if response == RESPONSE_OK:            
                    if self.__gui.dialog_cut.get_widget('radioCutBestCutlist').get_active() == True:
                        cut_action = Cut_action.BEST_CUTLIST
                    elif self.__gui.dialog_cut.get_widget('radioCutChooseCutlist').get_active() == True:
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

                self.__gui.dialog_cutlist.get_widget('treeviewCutlists').get_model().clear()                
                dom_cutlists, error_message = self.get_dom_from_cutlist(file_conclusion.uncut_avi)
                
                cutlists_found = False
                 
                if dom_cutlists==None:
                    self.__gui.message_error_box(error_message)
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
                    
                        self.__gui.dialog_cutlist.add_cutlist(data_array)
                
                    if cutlists_found:                        
                        self.__gui.dialog_cutlist.get_widget('labelCutlistFile').set_text(basename(file_conclusion.uncut_avi))
                        response = self.__gui.dialog_cutlist.run()
                        self.__gui.dialog_cutlist.hide()
                        
                        treeselection = self.__gui.dialog_cutlist.get_widget('treeviewCutlists').get_selection()  
                        
                        if treeselection.count_selected_rows()==0 or response != RESPONSE_OK:                            
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
            while events_pending():
                main_iteration(False)  
        
        fileoperations.remove('tmp.js')
        
        # successful
        return cut_avi, None
                        
    def action_play(self, filename):
        player = self.config.get('play', 'player')

        if not self.__cut_video.match(filename):
            self.__gui.message_error_box("Die ausgewählte Datei ist kein Video!")
            return 
            
        if player=='':
            self.__gui.message_error_box("Es ist kein Player angegeben!")
            return
        
        p = subprocess.Popen([player, filename])
    
    def action_cut_play(self, filename):
        mplayer = self.config.get('play', 'mplayer')
        
        if not self.__uncut_video.match(filename):
            self.__gui.message_error_box("Die ausgewählte Datei ist kein ungeschnittenes Video!")
            return 
            
        if mplayer=='':
            self.__gui.message_error_box("Der MPlayer ist nicht angegeben!")
            return
        
        # get best cutlist
        dom_cutlists, error_message = self.get_dom_from_cutlist(filename)
        
        best_cutlist = None
        
        if dom_cutlists==None:
            self.__gui.message_error_box(error_message)
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
                self.__gui.message_error_box("Keine Cutlist gefunden!")
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
            self.__gui.message_error_box("Verbindungsprobleme")
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
            self.__gui.message_error_box("Fehler in Cutlist: " + ErrorMessage)
            return
        except ConfigParser.NoOptionError, (ErrorNumber, ErrorMessage):
            self.__gui.message_error_box("Fehler in Cutlist: " + ErrorMessage)
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
        dialog = self.__gui.dialog_archive
       
        treeview_files = self.__gui.dialog_archive.get_widget('treeviewFilesRename')
        treestore_files = treeview_files.get_model()
        treeview_folders = self.__gui.dialog_archive.get_widget('treeviewFolders')
        treestore_folders = treeview_folders.get_model()
                
        self.__gui.dialog_archive.get_widget('labelFiles').set_text("%s Datei(en) zum Archivieren ausgewählt." % len(filenames))
        
        # fill rename tree
        dict_files_iter = {}        
        for f in filenames:
            iter = self.__gui.dialog_archive.append_row_treeviewFilesRename(basename(f))
            # keep relation between filename and iter
            dict_files_iter[f] = iter
            
        # fill tree of folders
        root = self.__gui.dialog_archive.append_row_treeviewFolders(None, self.config.get('folders', 'archive'))    
        self.tree_folders(root)        
        # select first node
        selection = treeview_folders.get_selection()
        selection.select_path(0)
        
        # expand
        treeview_folders.expand_all()
        
        result = dialog.run()

        if result == RESPONSE_OK:            
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
            
                new_name = join(dirname(f), new_name)
                fileoperations.rename(f, new_name)
                fileoperations.move_file(new_name, target_folder)   
                
                    
        dialog.hide()
                
        # clear treeview and listview
        treestore_folders.clear()
        treestore_files.clear()

    # recursive
    def tree_folders(self, parent):              
        dir = self.__gui.dialog_archive.get_widget('treeviewFolders').get_model().get_value(parent, 0)
            
        files = []
        files = listdir(dir)            

        for file in files:
            full_path = join(dir, file)
            
            if isdir(full_path):                
                iter = self.__gui.dialog_archive.append_row_treeviewFolders(parent, full_path)
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
        response, new_names = self.__gui.dialog_rename.init_and_run("Umbenennen", filenames)  
                
        if response:
            for f in filenames:
                new_name = join(dirname(f), new_names[f])
                
                if f.endswith('.avi') and not new_name.endswith('.avi'):
                    new_name+='.avi'
                    
                fileoperations.rename_file(f, new_name)

    def action_new_folder(self, filename):
        if isdir(filename):
            dirname = filename
        else:
            dirname = dirname(filename)

        response, new_names = self.__gui.dialog_rename.init_and_run("Neuer Ordner", ["Neuer Ordner"])

        if response and new_names["Neuer Ordner"] != "":            
            mkdir(join(dirname, new_names["Neuer Ordner"]))
            
    def run(self):
        self.__gui.main_window.show()      

        if self.config.get('folders', 'new_otrkeys') == "":      
            self.__gui.message_info_box("Dies ist offenbar das erste Mal, dass OTR-Verwaltung gestartet wird.\n\nEs müssen zunächst einige wichtige Einstellungen vorgenommen werden. Klicken Sie dazu auf OK.")
            self.__gui.preferences_window.show()
        
        self.__gui.run()

app = App()
app.run()
app.config.save()
