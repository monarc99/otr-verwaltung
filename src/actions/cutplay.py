#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from os.path import join, basename
import urllib

from baseaction import BaseAction
import cutlists as cutlists_management
from fileoperations import remove_file

class CutPlay(BaseAction):
    
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filename, mplayer, temp_folder, server, choose_cutlists_by, delete_cutlist):                
        if not mplayer:
            self.__gui.message_error_box("Der MPlayer ist nicht angegeben!")
            return
        
        # get best cutlist       
        def error_cb(error):
            self.__gui.message_error_box(error)
        
        cutlists = cutlists_management.download_cutlists(filename, server, choose_cutlists_by, error_cb) 
        
        if len(cutlists) == 0:            
            return
            
        best_cutlist = cutlists_management.get_best_cutlist(cutlists)
                
        # download cutlist and save it               
        local_filename, error = cutlists_management.download_cutlist(best_cutlist, server, filename)  
                
        if not local_filename:      
            self.__gui.message_error_box("Konnte Cutlist nicht herunterladen (%s). " % local_filename)
            return
        
        # get cuts
        cuts = cutlists_management.get_cuts_of_cutlist(local_filename)
        print cuts
        if type(cuts) != list: # error occured
            self.__gui.message_error_box(cuts)
            return
       
        # delete cutlist?        
        if delete_cutlist:
            remove_file(local_filename)  
        
        # make edl
        # http://www.mplayerhq.hu/DOCS/HTML/en/edl.html
        # [Begin Second] [End Second] [0=Skip/1=Mute]
        edl_filename = join(temp_folder, ".tmp.edl")
        f = open(edl_filename, "w")
        
        f.write("0 %s 0\n" % (cuts[0][1] - 1))        
        
        for count, start, duration in cuts:
            end = start + duration
            if count + 1 == len(cuts):
                f.write("%s 50000 0\n" % (end))
            else:
                f.write("%s %s 0\n" % (end, (cuts[count+1][1] - 1)))
        
        p = subprocess.Popen([mplayer, "-edl", edl_filename, filename])
