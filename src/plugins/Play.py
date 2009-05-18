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
        
        self.row_activate_id = self.gui.main_window.get_widget('treeview_files').connect('row-activated', self.on_row_activated)
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)        
        self.gui.main_window.get_widget('treeview_files').disconnect(self.row_activate_id)

    def configurate(self, dialog):
        dialog.vbox.set_spacing(4) 

        combobox_players = gtk.ComboBoxEntry()
        self.gui.set_model_from_list(combobox_players, ['vlc', 'mplayer', 'totem'])
        dialog.vbox.pack_start(combobox_players, expand=False)
                
        def on_combobox_players_changed(widget, data=None):
            self.Config['player'] = widget.child.get_text()
               
        combobox_players.connect('changed', on_combobox_players_changed)
           
        # current config
        combobox_players.child.set_text(self.Config['player'])
        
        return dialog
       
    # plugin methods
    def start_player(self):        
        filename = self.gui.main_window.get_selected_filenames()[0]
        
        try:        
            subprocess.Popen([self.Config['player'], filename])    
        except OSError:
            self.__gui.message_error_box("Es ist kein Player angegeben!")
    
    # signal methods
    def on_play_clicked(self, widget, data=None):       
        self.start_player()
    
    def on_row_activated(self, treeview, path, view_column):        
        if self.app.section in self.relevant_sections:
            self.start_player() 
