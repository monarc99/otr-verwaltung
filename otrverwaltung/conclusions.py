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

from constants import Action
import os.path

from otrverwaltung.cutlists import Cutlist
from otrverwaltung.constants import Action, Status
from otrverwaltung import path
from otrverwaltung import fileoperations
from otrverwaltung.GeneratorTask import GeneratorTask

class Decode:
    def __init__(self):
        self.status = -1
        self.message = ""
    
class Cut:
    def __init__(self):
        self.status = -1
        self.message = ""
        
        self.cut_action = -1                # manually, best cutlist ...
        self.cutlist = Cutlist()            # cutlist class instance

        # filled in by dialog_conclusion
        self.my_rating = -1                 # rating, when cut by cutlist        
        self.rename = ""                    # renamed filename
        self.archive_to = None              # directory, where the file should be archived
        self.create_cutlist = False         # create a cutlist?
        self.delete_uncut = True            # delete the uncut video after cut?

class FileConclusion:
    def __init__(self, action, otrkey="", uncut_video=""):
        self.action = action
        
        if action == Action.DECODE or action == Action.DECODEANDCUT:
            self.otrkey = otrkey
            self.decode = Decode()

        self.uncut_video = uncut_video
        
        if action == Action.CUT or action == Action.DECODEANDCUT:        
            self.cut_video = ""
            self.cut = Cut() 

    def get_extension(self):    
        return os.path.splitext(self.uncut_video)[1]
        
class ConclusionsManager:
    def __init__(self, app):
        self.app = app
        self.conclusions = []

    def add_conclusions(self, *args):
        for conclusion in args:
            self.conclusions.append(conclusion)
    
        if len(self.conclusions) == 1:
            text = "Eine Datei ist fertig."
        else:
            text = "%i Dateien sind fertig." % len(self.conclusions)

        self.app.gui.main_window.builder.get_object('label_conclusion').set_text(text)
        self.app.gui.main_window.builder.get_object('box_conclusion').show()

    def show_conclusions(self):
        conclusions = self.app.gui.dialog_conclusion._run(self.conclusions, self.app.rename_by_schema, self.app.config.get('general', 'folder_archive'))
        self.app.gui.main_window.builder.get_object('box_conclusion').hide()   
        self.conclusions = []
        
        # create cutlists            
        cutlists = []

        for conclusion in conclusions:
            if conclusion.action == Action.DECODE:
                continue

            print "[Conclusion] for file ", conclusion.uncut_video

            print "[Conclusion] Create cutlist?"
            if conclusion.cut.create_cutlist:
                print "[Conclusion] true"
                if "VirtualDub" in conclusion.cut.cutlist.intended_app:
                    intended_app_name = "VirtualDub"
                else:
                    intended_app_name = "Avidemux"

                conclusion.cut.cutlist.local_filename = conclusion.uncut_video + ".cutlist"
                conclusion.cut.cutlist.author = self.app.config.get('general', 'cutlist_username')
                conclusion.cut.cutlist.intended_version = open(path.getdatapath("VERSION"), 'r').read().strip()
                conclusion.cut.cutlist.smart = self.app.config.get('general', 'smart')                   

                conclusion.cut.cutlist.write_local_cutlist(conclusion.uncut_video, intended_app_name, conclusion.cut.my_rating)
                    
                cutlists.append(conclusion.cut.cutlist)
                                    
            # rename
            print "[Conclusion] Rename?"
            if conclusion.cut.rename:
                print "[Conclusion] true"
                extension = conclusion.get_extension()
                if not conclusion.cut.rename.endswith(extension):
                    conclusion.cut.rename += extension
                
                new_filename = os.path.join(self.app.config.get('general', 'folder_cut_avis'), conclusion.cut.rename.replace('/', '_'))
                new_filename = fileoperations.make_unique_filename(new_filename)
                    
                if conclusion.cut_video != new_filename:
                    conclusion.cut_video = fileoperations.rename_file(conclusion.cut_video, new_filename)
        
            # move cut video to archive
            print "[Conclusion] Move to archive?"
            if conclusion.cut.archive_to:
                print "[Conclusion] true"
                fileoperations.move_file(conclusion.cut_video, conclusion.cut.archive_to)
        
            # move uncut video to trash if it's ok
            print "[Conclusion] Move to trash?"
            if conclusion.cut.status == Status.OK and conclusion.cut.delete_uncut:                
                print "[Conclusion] true"
                if os.path.exists(conclusion.uncut_video):
                    # move to trash
                    target = self.app.config.get('general', 'folder_trash_avis')
                    fileoperations.move_file(conclusion.uncut_video, target)        
        
            # remove local cutlists      
            print "[Conclusion] Remove local cutlist?"
            if self.app.config.get('general', 'delete_cutlists'):                
                print "[Conclusion] true"
                if conclusion.cut.cutlist.local_filename and not conclusion.cut.create_cutlist:
                    if os.path.exists(conclusion.cut.cutlist.local_filename):
                        fileoperations.remove_file(conclusion.cut.cutlist.local_filename)
        
            
        # upload cutlists:
        def upload():
            error_messages = []

            for cutlist in cutlists:
                error_message = cutlist.upload(self.app.config.get('general', 'server'), self.app.config.get('general', 'cutlist_hash'))
                if error_message: 
                    error_messages.append(error_message)
                else:
                    if self.app.config.get('general', 'delete_cutlists'):
                        fileoperations.remove_file(cutlist.local_filename)
                 
            count = len(cutlists)
                
            message = "Es wurden %s/%s Cutlisten hochgeladen!" % (str(count - len(error_messages)), str(count))
            if len(error_messages) > 0:
                message += " (" + ", ".join(error_messages) + ")"

            yield message
                
        if len(cutlists) > 0:
            print "[Conclusion] Upload cutlists"
            if self.app.gui.question_box("Soll(en) %s Cutlist(en) hochgeladen werden?" % len(cutlists)):
                    
                def change_status(message):
                    self.app.gui.main_window.change_status(0, message)
                    
                GeneratorTask(upload, change_status).start()
          
        # rate cutlists                
        def rate():                    
            yield 0 # fake generator
            messages = []
            count = 0
            for conclusion in conclusions:                    
                if conclusion.action == Action.DECODE:
                    continue
                
                if conclusion.cut.my_rating > -1:
                    print "Rate with ", conclusion.cut.my_rating
                    success, message = conclusion.cut.cutlist.rate(conclusion.cut.my_rating, self.app.config.get('general', 'server'))
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
                
                self.app.gui.main_window.change_status(0, text)
        
        print "[Conclusion] Rate cutlists"
        GeneratorTask(rate).start()
