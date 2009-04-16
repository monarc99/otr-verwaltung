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

    def do(self, filename, mplayer, temp_folder, server, choose_cutlists_by, cutlist_mp4_as_hq, delete_cutlist):                
        # FIXME or not: no error handling
    
        if not mplayer:
            self.__gui.message_error_box("Der MPlayer ist nicht angegeben!")
            return
             
        cutlists = cutlists_management.download_cutlists(filename, server, choose_cutlists_by, cutlist_mp4_as_hq) 
        cutlist = cutlists_management.get_best_cutlist(cutlists)
        cutlist.download(server, filename)
        cutlist.read_cuts()       
       
        # delete cutlist?        
        if delete_cutlist:
            remove_file(cutlist.local_filename)  
       
        # make edl
        # http://www.mplayerhq.hu/DOCS/HTML/en/edl.html
        # [Begin Second] [End Second] [0=Skip/1=Mute]
        edl_filename = join(temp_folder, ".tmp.edl")
        f = open(edl_filename, "w")
       
        f.write("0 %s 0\n" % (cutlist.cuts[0][1] - 1))        
       
        for count, start, duration in cutlist.cuts:
            end = start + duration
            if count + 1 == len(cutlist.cuts):
                f.write("%s 50000 0\n" % (end))
            else:
                f.write("%s %s 0\n" % (end, (cutlist.cuts[count+1][1] - 1)))
       
        p = subprocess.Popen([mplayer, "-edl", edl_filename, filename])


