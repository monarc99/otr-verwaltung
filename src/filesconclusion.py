#!/usr/bin/env python
# -*- coding: utf-8 -*-

from constants import Action

class Decode:
    def __init__(self):
        self.status = -1
        self.message = ""
    
class Cut:
    def __init__(self):
        self.status = -1
        self.message = ""
        
        self.cut_action = -1                # manually, best cutlist ...
        self.cutlist = -1                   # id of cutlist
        self.rating = -1                    # rating, when cut by cutlist
        self.local_cutlist = ""             # filename of local cutlist
        self.rename = None                  # 
        self.executable = ""                # executable of cut program, only when manually
        
        self.create_cutlist = False         # create cutlist?
        self.cutlist_cuts = None            # (count, start, duration) list
        self.create_cutlist_error = ""      # couldn't get cuts from project file
                                   
        self.cutlist_information = {        # used, when manually cut
                'rating' : 0,
                'wrong_content': False,
                'actual_content': "",
                'missing_beginning': False,
                'missing_ending': False,
                'other_error': False,
                'other_error_description': "",
                'suggested': "",
                'comment': ""
            }         
        
        self.delete_uncut = True

class FileConclusion:
    def __init__(self, action, otrkey="", uncut_avi=""):
        if action == Action.DECODE or action == Action.DECODEANDCUT:
            self.otrkey = otrkey
            self.decode = Decode()
        
        self.uncut_avi = uncut_avi
        
        if action == Action.CUT or action == Action.DECODEANDCUT:
            self.cut_avi = ""
            self.cut = Cut() 
