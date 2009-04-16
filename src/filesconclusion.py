#!/usr/bin/env python
# -*- coding: utf-8 -*-

from constants import Action
import os.path

from cutlists import Cutlist

class Decode:
    def __init__(self):
        self.status = -1
        self.message = ""
    
class Cut:
    def __init__(self):
        self.status = -1
        self.message = ""
        self.create_cutlist_error = ""      # couldn't get cuts from project file                                           
        
        self.cut_action = -1                # manually, best cutlist ...
        self.cutlist = Cutlist()            # cutlist class instance

        # filled in by dialog_conclusion
        self.my_rating = None               # rating, when cut by cutlist        
        self.rename = 0                     # by autoname, filename ...
        self.create_cutlist = False         # create a cutlist?
        self.delete_uncut = True            # delete the uncut avi after cut?

class FileConclusion:
    def __init__(self, action, otrkey="", uncut_avi=""):
        if action == Action.DECODE or action == Action.DECODEANDCUT:
            self.otrkey = otrkey
            self.decode = Decode()
        
        self.uncut_avi = uncut_avi
        self.extension = os.path.splitext(uncut_avi)[1]

        print "Adding: ", self.extension

        if action == Action.CUT or action == Action.DECODEANDCUT:
            self.cut_avi = ""
            self.cut = Cut() 
