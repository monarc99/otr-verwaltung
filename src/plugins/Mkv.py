#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import subprocess
import time

from pluginsystem import Plugin

from constants import Section

class Mkv(Plugin):
    Name = "MKV"
    Desc = "Wandelt avi-Dateien mit Hilfe von mkvmerge in mkv-Dateien um."
    Author = "Benjamin Elbers"
    Configurable = True
    Config = { 'mkvmerge': 'mkvmerge' }
        
    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('mkv.png')), 'In MKV konvertieren', [Section.VIDEO_UNCUT, Section.VIDEO_CUT, Section.ARCHIVE])
        self.toolbutton.connect('clicked', self.on_mkv_clicked)                        
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)
    
    def configurate(self, dialog):
        dialog.vbox.set_spacing(4) 

        # TODO: optionen für hq und avi?
        # TODO: automatisch umwandeln nach schneiden? (option?)

        dialog.vbox.pack_start(gtk.Label("Name von mkvmerge:"), expand=False)
        entry_mkvmerge = gtk.Entry()
        dialog.vbox.pack_start(entry_mkvmerge, expand=False)
                
        def on_entry_mkvmerge_changed(widget, data=None):
            self.Config['mkvmerge'] = widget.get_text()
               
        entry_mkvmerge.connect('changed', on_entry_mkvmerge_changed)
           
        # current config
        entry_mkvmerge.set_text(self.Config['mkvmerge'])
        
        return dialog

    def on_mkv_clicked(self, widget, data=None):
        for filename in self.gui.main_window.get_selected_filenames():
            p = subprocess.Popen([self.Config['mkvmerge'], "-o", filename + ".mkv", filename], stdout=subprocess.PIPE)
            
            while p.poll() == None:
                time.sleep(1)
                
                # read progress from stdout 
                # p.stdout.read()
                
                while gtk.events_pending():
                    gtk.main_iteration(False)
            # TODO: WRITE nice bindings to progress bar        
            #           main_window.show_tasks
            #           main_window.hide_tasks
            #           main_window.set_tasks(text=None, progress=None)
            
