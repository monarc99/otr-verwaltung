#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, subprocess

from pluginsystem import Plugin

from constants import Section

class Play(Plugin):
    Name = "Abspielen"
    Desc = "Spielt Video-Dateien ab."
    Author = "Benjamin Elbers"
    Configurable = True
    Config = { 'player': '' }
        
    def enable(self):    
        self.relevant_sections = [Section.VIDEO_UNCUT, Section.VIDEO_CUT, Section.ARCHIVE]

        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('play.png')), 'Abspielen', self.relevant_sections)
        self.toolbutton.connect('clicked', self.on_play_clicked)        
        
        self.gui.main_window.get_widget('treeview_files').connect('row-activated', self.on_row_activated)
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)
    
    def configurate(self):
        print "config"
       
    # plugin methods
    def start_player(self, filename):
        player = self.Config['player']
        
        try:        
            subprocess.Popen([player, filename])    
        except OSError:
            self.__gui.message_error_box("Es ist kein Player angegeben!")
    
    def on_play_clicked(self, widget, data=None):
        # get filename
        filename = '' 
        
        self.start_player(filename)
    
    def on_row_activated(self, treeview, path, view_column):
        
        if self.app.section in self.relevant_sections:
            filename = ''
            
            self.start_player(filename)
        
