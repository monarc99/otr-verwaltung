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

import subprocess, time
import os.path
import gtk

from otrverwaltung.pluginsystem import Plugin

import otrverwaltung.cutlists as cutlists_management
from otrverwaltung import fileoperations
from otrverwaltung.constants import Section

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
        
        error, cutlists = cutlists_management.download_cutlists(filename, self.app.config.get('general', 'server'), self.app.config.get('general', 'choose_cutlists_by'), self.app.config.get('general', 'cutlist_mp4_as_hq')) 
        if error:
            return
            
        cutlist = cutlists_management.get_best_cutlist(cutlists)
        cutlist.download(self.app.config.get('general', 'server'), filename)
        cutlist.read_cuts()       
       
        # delete cutlist?        
        if self.app.config.get('general', 'delete_cutlists'):
            fileoperations.remove_file(cutlist.local_filename)  
       
        # make edl
        # http://www.mplayerhq.hu/DOCS/HTML/en/edl.html
        # [Begin Second] [End Second] [0=Skip/1=Mute]
        edl_filename = os.path.join(self.app.config.get('general', 'folder_uncut_avis'), ".tmp.edl")
        f = open(edl_filename, "w")
       
        f.write("0 %s 0\n" % (cutlist.cuts_seconds[0][0] - 1))        
       
        for count, (start, duration) in enumerate(cutlist.cuts_seconds):
            end = start + duration
            if count + 1 == len(cutlist.cuts_seconds):
                f.write("%s 50000 0\n" % (end))
            else:
                f.write("%s %s 0\n" % (end, (cutlist.cuts_seconds[count+1][0] - 1)))
        f.close()
        
        p = subprocess.Popen([self.app.config.get_program('mplayer'), "-edl", edl_filename, filename])                
        
        while p.poll() == None:
            time.sleep(1)
            while gtk.events_pending():
                gtk.main_iteration(False)

        fileoperations.remove_file(edl_filename)
