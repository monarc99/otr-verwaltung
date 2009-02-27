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
        
        self.cut_action = -1
        self.cutlist = -1
        self.rating = -1
        self.local_cutlist = ""
        
        self.delete_uncut = False

class FileConclusion:
    def __init__(self, action, otrkey="", uncut_avi=""):
        if action == Action.DECODE or action == Action.DECODEANDCUT:
            self.otrkey = otrkey
            self.decode = Decode()
        
        self.uncut_avi = uncut_avi
        
        if action == Action.CUT or action == Action.DECODEANDCUT:
            self.cut_avi = ""
            self.cut = Cut()
            
