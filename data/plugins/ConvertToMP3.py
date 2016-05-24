# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2016 Malte Kiefer <malte.kiefer@mailgermania.de>
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

from otrverwaltung import fileoperations
from otrverwaltung.constants import Section

class ConvertToMP3(Plugin):
    Name = "ConvertToMP3"
    Desc = "Mit diesem Plugin können Sie Videodateien in MP3 Audiodateien umwandeln."
    Author = "Malte Kiefer"
    Configurable = False
        
    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('music.png')), 'ConvertToMP3', [Section.VIDEO_CUT, Section.ARCHIVE])
        self.toolbutton.connect('clicked', self.on_converttomp3_clicked)                
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)               
          
    # plugin methods
  
    # signal methods
    def self.on_converttomp3_clicked(self, widget, data=None):   
        filename = self.gui.main_window.get_selected_filenames()[0]
        
        ffmpeg -i filename -vn -ar 44100 -ac 2 -ab 320k -f mp3 filename.mp3
        
        self.gui.main_window.change_status(0, "Erfolgreich %s umgewandelt." % (filename)

