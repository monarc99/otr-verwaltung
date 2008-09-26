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
import os
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
import configParser
from files_conclusion import FileConclusion
from constants import Section, Action, Cut_action, Save_Email_Password, Status

class App:
    
    def __init__(self):             
        # read configs
        config = configParser.Config() 
        self.config_dic = config.read(os.path.join(sys.path[0], ".otr-conf"))

        self.search_text = ""

        # load gui
        self.gui = gui.GUI(self, os.path.join(sys.path[0], "otr.ui"))       
        
        # show undecoded otrkeys         
        self.show_section(Section.OTRKEY)
        
        # regex
        self.uncut_video = re.compile('.*_([0-9]{2}\.){2}([0-9]){2}_([0-9]){2}-([0-9]){2}_.*_([0-9])*_TVOON_DE.mpg\.(avi|HQ\.avi|mp4)$')
        self.cut_video = re.compile('.*(avi|mp4)$')
        
        
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
        self.gui.set_toolbar(section)
                
        self.gui.main_window['treeviewFiles_store'].clear()
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
            self.gui.main_window['treeviewFiles'].expand_all()

        if len(files)>0: # this is not executed, when the section is "Archive"
            if len(files)==1:
                text += " (1 Datei)"
            else:
                text += " (%s Dateien) " % len(files)
            
            files.sort()
            # put filenames into treestore
            for f in files:
                self.gui.append_row_treeviewFiles(None, f)

        # set message textfilenames_action_status[file][action][0]
        self.gui.main_window['labelMessage'].set_text(text)
             
    # helper for different section
    def section_otrkey(self):
        text = "Diese Dateien wurden noch nicht dekodiert." 
        path = self.config_dic['folders']['new_otrkeys']
        
        if self.config_dic['folders']['new_otrkeys'] == "":      
            return text, []
        
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".otrkey") and self.search(f)]                           
            
        return (text, files)
         
    def section_avi_uncut(self):
        text = "Diese Dateien wurden noch nicht geschnitten."
        path = self.config_dic['folders']['new_otrkeys']
        
        files = [os.path.join(path, f) for f in os.listdir(path) if self.uncut_video.match(f) and self.search(f)]
            
        return (text, files)
        
    def section_avi_cut(self):
        text = "Diese avi-Dateien sind fertig geschnitten."
        if self.config_dic['common']['use_archive']:
            text += " Sie können ins Archiv verschoben werden."
                
        path = self.config_dic['folders']['new_otrkeys']
        
        files = []                
        for f in os.listdir(path):
            if not self.uncut_video.match(f):
                if self.cut_video.match(f):
                    if self.search(f):
                        files += [os.path.join(path, f)]
        
        return (text, files)
        
    def section_trash(self):
        text = "Diese otrkey- und avi-Dateien wurden bereits dekodiert bzw. geschnitten. Sie können normalerweise gelöscht werden."
        path = self.config_dic['folders']['trash']
                    
        files = [os.path.join(path, f) for f in os.listdir(path) if (f.endswith('.otrkey') or f.endswith('.avi')) and self.search(f)]
                
        return (text, files)

    def section_archive(self):
        text = "Diese Dateien wurden ins Archiv verschoben."

        path = self.config_dic['folders']['archive']
               
        self.tree(None, path)
        
        return text            
                 
    # recursive function for archive to add folders and files with a tree structure
    def tree(self, parent, path=None):              
        if parent!=None:            
            dir = self.gui.get_filename(parent)
        else:  # base path (archive directory)
            dir = path
            
        files = []
        files = os.listdir(dir)            

        for file in files:
            full_path = os.path.join(dir, file)
            
            if os.path.isdir(full_path):                
                iter = self.gui.append_row_treeviewFiles(parent, full_path)
                self.tree(iter)
            else:
                if file.endswith('.avi'):
                    if self.search(file):
                        self.gui.append_row_treeviewFiles(parent, full_path)

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
                       
    def start_search(self, search):
        self.search_text = search.lower()
        
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
        for root, dirs, wfiles in os.walk(self.config_dic['folders']['archive']):
            for f in wfiles:
                if f.endswith('.avi') and self.search(f):
                    files += [os.path.join(root, f)]

        count = len(files)
        if count > 0:
            counts[Section.ARCHIVE] = "(%s)" % count
        else:
            counts[Section.ARCHIVE] = ""
        
        self.show_section(self.section)                   
        return counts
    
    def stop_search(self):
        self.search_text = ""
        self.show_section(self.section)
        
    def search(self, f):
        if self.search_text == "":
            return True
        else:    
            if self.search_text in f.lower():
                return True
            else:
                return False
        
    ###
    ### Actions
    ###        
    
    def perform_action(self, action, filenames):
        """ Performs an action (toolbar, context menu, etc.) """
        
        if len(filenames) == 0 and action!=Action.NEW_FOLDER:        
            self.gui.message_box("Es sind keine Dateien markiert!", gtk.MESSAGE_INFO, gtk.BUTTONS_OK)   
            return
        
        # different actions:
        if action==Action.DECODE or action==Action.CUT or action==Action.DECODEANDCUT:
              
            # (re)build progressbar dialog
            dialog = self.gui.build_action_window(len(filenames), action)
            
            # create file_conclusions array        
            file_conclusions = []
                
            if action==Action.DECODE or action==Action.DECODEANDCUT:
                for otrkey in filenames:
                    file_conclusions.append(FileConclusion(action, otrkey=otrkey))
                
            if action==Action.CUT:
                for uncut_avi in filenames:
                    file_conclusions.append(FileConclusion(action, uncut_avi=uncut_avi))
                
            # decode files                    
            if action==Action.DECODE or action==Action.DECODEANDCUT:
                if self.action_decode(file_conclusions)==False: 
                    return
            
            # cut files
            if action==Action.CUT or action==Action.DECODEANDCUT:
                if self.action_cut(file_conclusions, action)==False:
                    return                    
                
            # hide action dialog
            self.gui.windows['dialog_action'].hide()          
                
            # show conclusion
            dialog = self.gui.build_conclusion_dialog(file_conclusions, action)
            dialog.run()         
            
            # rate...
            #
            #
            #
 
            # update section
            self.gui.windows['main_window'].show()
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
                self.action_new_folder(self.config_dic['folders']['archive'])
            else:
                self.action_new_folder(filenames[0])
            self.show_section(self.section)
        
        elif action==Action.CUT_PLAY:
            self.action_cut_play(filenames[0])
            
        elif action==Action.REAL_DELETE:
            self.action_real_delete(filenames)
            self.show_section(self.section)
      
    # helpers for actions                   
    def action_decode(self, file_conclusions):           
        
        # no decoder        
        if not "decode" in self.config_dic['decode']['path']: # no decoder specified
            # dialog box: no decoder
            self.gui.message_box("Es ist kein korrekter Dekoder angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)   
            return False
        
        # retrieve email and password
        # user did not save email and password
        if self.config_dic['decode']['save_email_password'] == Save_Email_Password.DONT_SAVE:
            # let the user type in his data through a dialog
            response = self.gui.windows['dialog_email_password'].run()
            self.gui.windows['dialog_email_password'].hide() 
            
            if response==gtk.RESPONSE_OK:
                email = self.gui.dialog_email_password['entryDialogEMail'].get_text()
                password = self.gui.dialog_email_password['entryDialogPassword'].get_text()                               
            else: # user pressed cancel
                return False
                         
        else: # user typed email and password in         
            email = self.config_dic['decode']['email']
            password = base64.b64decode(self.config_dic['decode']['password']) 
        
        # start decoding, show "action" window
        # now this method may not return "False"
        self.gui.windows['main_window'].hide()
        self.gui.windows['dialog_action'].show()     
                 
        # decode each file
        for count, file_conclusion in enumerate(file_conclusions):
                   
            command = "%s -i %s -e %s -p %s -o %s" % (self.config_dic['decode']['path'], file_conclusion.otrkey, email, password, self.config_dic['folders']['new_otrkeys'])
            if self.config_dic['decode']['correct'] == 0:
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
                    # set progress on decode progressbar
                    progress = (progress/100.) / len(file_conclusions) + count * (1. / len(file_conclusions))
                    self.gui.dialog_action['progressbar_decode'].set_fraction(progress)
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
            
                # TODO: Verschieben auf nach dem zeigen der zusammenfassung?            
                # move to trash
                target = self.config_dic['folders']['trash']
                os.rename(file_conclusion.otrkey, os.path.join(target, os.path.basename(file_conclusion.otrkey)))
            else:            
                file_conclusion.decode.status = Status.ERROR
                file_conclusion.decode.message = error_message
                
        return True

    def action_cut(self, file_conclusions, action):               
        # start cutting, show "action" window
        # now this method may not return "False"
        self.gui.windows['main_window'].hide()
        self.gui.windows['dialog_action'].show()       
        
        for count, file_conclusion in enumerate(file_conclusions):

            # file correctly decoded?            
            if action==Action.DECODEANDCUT:
                if file_conclusion.decode.status == Status.ERROR:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Datei wurde nicht dekodiert."
                    continue

            # how should the file be cut?
            cut_action = None
            if self.config_dic['cut']['cut_action'] == Cut_action.ASK:
                self.gui.dialog_cut['labelCutFile'].set_text(os.path.basename(file_conclusion.uncut_avi))
                self.gui.dialog_cut['labelWarning'].set_text('Wichtig! Die Datei muss im Ordner "%s" und unter einem neuen Namen gespeichert werden, damit das Programm erkennt, dass diese Datei geschnitten wurde!' % self.config_dic['folders']['new_otrkeys'])

                response = self.gui.windows['dialog_cut'].run()
                self.gui.windows['dialog_cut'].hide()
                
                if response == gtk.RESPONSE_OK:            
                    if self.gui.dialog_cut['radioCutBestCutlist'].get_active() == True:
                        cut_action = Cut_action.BEST_CUTLIST
                    elif self.gui.dialog_cut['radioCutChooseCutlist'].get_active() == True:
                        cut_action = Cut_action.CHOOSE_CUTLIST
                    else:                    
                        cut_action = Cut_action.MANUALLY
                else:
                    file_conclusion.cut.status = Status.NOT_DONE
                    file_conclusion.cut.message = "Abgebrochen"
                    continue
            
            else: # !=ASK
                cut_action = self.config_dic['cut']['cut_action']
 
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
                            file_conclusion.cutlist = best_cutlist                            
                
            elif cut_action == Cut_action.CHOOSE_CUTLIST:
                # download all cutlist and display them to
                # the user

                self.gui.dialog_cutlist['treeviewCutlists_store'].clear()                
                dom_cutlists, error_message = self.get_dom_from_cutlist(file_conclusion.uncut_avi)
                
                cutlists_found = False
                 
                if dom_cutlists==None:
                    self.gui.message_box(error_message, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
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
                    
                        self.gui.add_cutlist(data_array)
                
                    if cutlists_found:                        
                        self.gui.dialog_cutlist['labelCutlistFile'].set_text(os.path.basename(file_conclusion.uncut_avi))
                        response = self.gui.windows['dialog_cutlist'].run()
                        self.gui.windows['dialog_cutlist'].hide()
                        
                        treeselection = self.gui.dialog_cutlist['treeviewCutlists'].get_selection()  
                        
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
                                file_conclusion.cutlist = chosen_cutlist         
                                                                                        
                    else: # no cutlist in xml
                        file_conclusion.cut.status = Status.NOT_DONE
                        file_conclusion.cut.message = "Keine Cutlist gefunden."

            elif cut_action == Cut_action.MANUALLY: # MANUALLY
                command = "%s --load %s >>/dev/null" %(self.config_dic['cut']['avidemux'], avi)
                avidemux = subprocess.Popen(command, shell=True)    
                while avidemux.poll()==None:
                    # wait
                    pass
                    
                file_conclusion.cut.status = Status.OK
        
            # TODO: Verschieben auf nach dem zeigen der zusammenfassung?            
            # action after cut
            status = file_conclusion.cut.status
            
            if status == Status.OK:
                # move to trash
                target = self.config_dic['folders']['trash']
                os.rename(file_conclusion.uncut_avi, os.path.join(target, os.path.basename(file_conclusion.uncut_avi)))
             
            progress = 1./len(file_conclusions) + count * (1. / len(file_conclusions))
            self.gui.dialog_action['progressbar_cut'].set_fraction(progress)
        
        # after iterating over all items:
        return True
       
    def get_dom_from_cutlist(self, avi):
        size = os.path.getsize(avi)    
        url = self.config_dic['cut']['server'] + "getxml.php?version=0.9.8.0&ofsb=" + str(size)

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
        print "Downloading cutlist ", cutlist, " from ", self.config_dic['cut']['server'], " for ", filename
        url = self.config_dic['cut']['server'] + "getfile.php?id=" + str(cutlist)
        
        # save cutlist to folder
        local_filename = os.path.join(self.config_dic['folders']['new_otrkeys'], os.path.basename(filename) + ".cutlist")
        
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
        
        os.remove('tmp.js')
        
        # successful
        return cut_avi, None
                        
    def action_play(self, filename):
        player = self.config_dic['play']['player']

        if not self.cut_video.match(filename):
            self.gui.message_box("Die ausgewählte Datei ist kein Video!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return 
            
        if player=='':
            self.gui.message_box("Es ist kein Player angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        p = subprocess.Popen([player, filename])
    
    def action_cut_play(self, filename):
        mplayer = self.config_dic['play']['mplayer']
        
        if not self.uncut_video.match(filename):
            self.gui.message_box("Die ausgewählte Datei ist kein ungeschnittenes Video!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return 
            
        if mplayer=='':
            self.gui.message_box("Der MPlayer ist nicht angegeben!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        
        # get best cutlist
        dom_cutlists, error_message = self.get_dom_from_cutlist(filename)
        
        best_cutlist = None
        
        if dom_cutlists==None:
            self.gui.message_box(error_message, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
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
                self.gui.message_box("Keine Cutlist gefunden!", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
                return
            else: 
                sort_cutlists = cutlists.items()
                sort_cutlists.sort(key=lambda x: x[1], reverse=True) # first is the best
                       
                best_cutlist = sort_cutlists[0][0] # get first (=the best) cutlist; from the tuple, get the first (id) item
                
        # download cutlist + save it
        url = self.config_dic['cut']['server'] + "getfile.php?id=" + str(best_cutlist)        
        local_filename = os.path.join(self.config_dic['folders']['new_otrkeys'], os.path.basename(filename) + ".cutlist")
        
        try:
            local_filename, headers = urllib.urlretrieve(url, local_filename)
        except IOError:
            self.gui.message_box("Verbindungsprobleme", gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
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
            self.gui.message_box("Fehler in Cutlist: " + ErrorMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
            return
        except ConfigParser.NoOptionError, (ErrorNumber, ErrorMessage):
            self.gui.message_box("Fehler in Cutlist: " + ErrorMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE)
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
        dialog = self.gui.windows['dialog_archive']
        treeview_files = self.gui.dialog_archive['treeviewFilesRename']
        treestore_files = self.gui.dialog_archive['treeviewFilesRename_store']
        treeview_folders = self.gui.dialog_archive['treeviewFolders']
        treestore_folders = self.gui.dialog_archive['treeviewFolders_store']
                
        self.gui.dialog_archive['labelFiles'].set_text("%s Datei(en) zum Archivieren ausgewählt." % len(filenames))
        
        # fill rename tree
        dict_files_iter = {}        
        for f in filenames:
            iter = self.gui.append_row_treeviewFilesRename(os.path.basename(f))
            # keep relation between filename and iter
            dict_files_iter[f] = iter
            
        # fill tree of folders  
        root = self.gui.append_row_treeviewFolders(None, self.config_dic['folders']['archive'])    
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
            
                target = os.path.join(target_folder, new_name)
                print "Moving: ", f, " TO ", target
                os.rename(f, target)   
                    
        dialog.hide()
                
        # clear treeview and listview
        treestore_folders.clear()
        treestore_files.clear()

    # recursive
    def tree_folders(self, parent):              
        dir = self.gui.dialog_archive['treeviewFolders_store'].get_value(parent, 0)
            
        files = []
        files = os.listdir(dir)            

        for file in files:
            full_path = os.path.join(dir, file)
            
            if os.path.isdir(full_path):                
                iter = self.gui.append_row_treeviewFolders(parent, full_path)
                self.tree_folders(iter)

       
    def action_delete(self, filenames):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.gui.question_box(message + "in den Müll verschoben werden?"):
            for f in filenames:
                target = self.config_dic['folders']['trash']
                os.rename(f, os.path.join(target, os.path.basename(f)))
                
    def action_real_delete(self, filenames):
        if len(filenames) == 1:
            message = "Es ist eine Datei ausgewählt. Soll diese Datei "
        else:
            message = "Es sind %s Dateien ausgewählt. Sollen diese Dateien " % len(filenames)
        
        if self.gui.question_box(message + "endgültig gelöscht werden?"):
            for f in filenames:
                os.remove(f)
    
    def action_restore(self, filenames):
        for f in filenames:
            os.rename(f, os.path.join(self.config_dic['folders']['new_otrkeys'], os.path.basename(f)))        
    
    def action_rename(self, filenames):
        dialog = self.gui.windows['dialog_rename']
        vbox = self.gui.dialog_rename['vboxRename']
        
        entries = {}
        for f in filenames:
            entries[f] = gtk.Entry()
            entries[f].set_text(os.path.basename(f))
            entries[f].show()
            vbox.pack_start(entries[f])
        
        dialog.set_title("Umbenennen")    
        if dialog.run() == gtk.RESPONSE_OK:            
            for f in filenames:
                new_name = os.path.join(os.path.dirname(f), entries[f].get_text())
                
                if f.endswith('.avi') and not new_name.endswith('.avi'):
                    new_name+='.avi'
                    
                os.rename(f, new_name)
        
        dialog.hide()
            
        # remove entry widgets
        for f in entries:
            vbox.remove(entries[f])
                               
    def action_new_folder(self, filename):
        if os.path.isdir(filename):
            dirname = filename
        else:
            dirname = os.path.dirname(filename)

        dialog = self.gui.windows['dialog_rename']
        vbox = self.gui.dialog_rename['vboxRename']

        entry = gtk.Entry()
        entry.show()
        vbox.pack_start(entry)
        dialog.set_title("Neuer Ordner")
        
        if dialog.run()==gtk.RESPONSE_OK and entry.get_text!="":            
            os.mkdir(os.path.join(dirname, entry.get_text()))
            
        dialog.hide()
        
        vbox.remove(entry)
        
    def main(self):
        self.gui.run()
        config = configParser.Config() 
        config.save(".otr-conf", self.config_dic)   

app = App()
app.main()
