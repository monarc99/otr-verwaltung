#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess, time
import os.path
import gtk

from pluginsystem import Plugin

import cutlists as cutlists_management
import fileoperations
from constants import Section

class CutPlay(Plugin):
    Name = "Geschnittenes Abspielen"
    Desc = "Spielt Video-Dateien mit Hilfe von Cutlisten geschnitten ab, ohne jedoch die Datei zu schneiden. Es werden die Server-Einstellungen von OTR-Verwaltung benutzt."
    Author = "Benjamin Elbers"
    Configurable = False
        
    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('play.png')), 'Geschnitten Abspielen', [Section.VIDEO_UNCUT])
        self.toolbutton.connect('clicked', self.on_cut_play_clicked)                
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)               
          
    # plugin methods
  
    # signal methods
    def on_cut_play_clicked(self, widget, data=None):   
        filename = self.gui.main_window.get_selected_filenames()[0]
        
        error, cutlists = cutlists_management.download_cutlists(filename, self.app.config.get('server'), self.app.config.get('choose_cutlists_by'), self.app.config.get('cutlist_mp4_as_hq')) 
        if error:
            return
            
        cutlist = cutlists_management.get_best_cutlist(cutlists)
        cutlist.download(self.app.config.get('server'), filename)
        cutlist.read_cuts()       
       
        # delete cutlist?        
        if self.app.config.get('delete_cutlists'):
            fileoperations.remove_file(cutlist.local_filename)  
       
        # make edl
        # http://www.mplayerhq.hu/DOCS/HTML/en/edl.html
        # [Begin Second] [End Second] [0=Skip/1=Mute]
        edl_filename = os.path.join(self.app.config.get('folder_uncut_avis'), ".tmp.edl")
        f = open(edl_filename, "w")
       
        f.write("0 %s 0\n" % (cutlist.cuts[0][1] - 1))        
       
        for count, start, duration in cutlist.cuts:
            end = start + duration
            if count + 1 == len(cutlist.cuts):
                f.write("%s 50000 0\n" % (end))
            else:
                f.write("%s %s 0\n" % (end, (cutlist.cuts[count+1][1] - 1)))
        f.close()
        
        p = subprocess.Popen([self.app.config.get('mplayer'), "-edl", edl_filename, filename])                
        
        while p.poll() == None:
            time.sleep(1)
            while gtk.events_pending():
                gtk.main_iteration(False)

        fileoperations.remove_file(edl_filename)
