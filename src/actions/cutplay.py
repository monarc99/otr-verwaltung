#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import subprocess
from os.path import join, basename
import urllib

from baseaction import BaseAction
import cutlists as cutlists_management

class CutPlay(BaseAction):
    
    def __init__(self, gui):
        self.update_list = False
        self.__gui = gui

    def do(self, filename, mplayer, new_otrkeys_folder, server):                
        if not mplayer:
            self.__gui.message_error_box("Der MPlayer ist nicht angegeben!")
            return
        
        # get best cutlist       
        def error_cb(error):
            self.__gui.message_error_box(error)
        
        cutlists = cutlists_management.download_cutlists(filename, server, error_cb) 
        
        if len(cutlists) == 0:            
            return
            
        best_cutlist = cutlists_management.get_best_cutlist(cutlists)
                
        # download cutlist and save it
        url = server + "getfile.php?id=" + str(best_cutlist)        
        local_filename = join(new_otrkeys_folder, basename(filename) + ".cutlist")
        
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
