#!/usr/bin/python
# -*- coding: utf-8 -*-

import gtk, subprocess

from otrverwaltung.pluginsystem import Plugin

from otrverwaltung.constants import Section

class Play(Plugin):
    Name = "Abspielen"
    Desc = "Spielt Video-Dateien ab."
    Author = "Benjamin Elbers"
    Configurable = False
        
    def enable(self):    
        self.relevant_sections = [Section.VIDEO_UNCUT, Section.VIDEO_CUT, Section.ARCHIVE]

        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('play.png')), 'Abspielen', self.relevant_sections)
        self.toolbutton.connect('clicked', self.on_play_clicked)        
        
        self.row_activate_id = self.gui.main_window.builder.get_object('treeview_files').connect('row-activated', self.on_row_activated)
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)        
        self.gui.main_window.builder.get_object('treeview_files').disconnect(self.row_activate_id)
       
    # plugin methods
    def start_player(self):        
        filename = self.gui.main_window.get_selected_filenames()[0]
        self.app.play_file(filename)
    
    # signal methods
    def on_play_clicked(self, widget, data=None):       
        self.start_player()
    
    def on_row_activated(self, treeview, path, view_column):        
        if self.app.section in self.relevant_sections:
            self.start_player() 
