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
        if action == Action.DECODE or action == Action.DECODEANDCUT:
            self.otrkey = otrkey
            self.decode = Decode()
        
        self.uncut_video = uncut_video

        if action == Action.CUT or action == Action.DECODEANDCUT:
            self.cut_video = ""
            self.cut = Cut() 

    def get_extension(self):    
        return os.path.splitext(self.uncut_video)[1]
