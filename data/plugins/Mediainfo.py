#!/usr/bin/env python
# -*- coding: utf-8 -*-

from otrverwaltung.pluginsystem import Plugin
from otrverwaltung.constants import Section
import gtk, subprocess, os.path

class Mediainfo(Plugin):
	Name = "MediaInfo"
	Desc = "Analyse der Mediendatei"
	Author = "monarc99"
        Configurable = True
        Config = { 'mediainfo': 'mediainfo-gui' }

	def enable(self):
		self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('mediainfo.png')), 'MediaInfo', [Section.VIDEO_UNCUT, Section.VIDEO_CUT, Section.ARCHIVE, Section.TRASH])
		self.toolbutton.connect('clicked', self.mediainfo)

	def disable(self):
		self.gui.main_window.remove_toolbutton(self.toolbutton)

        def configurate(self, dialog):
            dialog.vbox.set_spacing(4) 
        
            dialog.vbox.pack_start(gtk.Label("Aufrufname der mediainfo GUI:"), expand=False)

            entry_mediainfo = gtk.Entry()
            dialog.vbox.pack_start(entry_mediainfo, expand=False)
            def on_entry_mediainfo_changed(widget, data=None):
                self.Config['mediainfo'] = widget.get_text()
            entry_mediainfo.connect('changed', on_entry_mediainfo_changed)

            # current config
            entry_mediainfo.set_text(self.Config['mediainfo'])
		
            return dialog 
		
	def mediainfo(self, widget):
		""" Öffne die Datei mit mediainfo """

                args = self.gui.main_window.get_selected_filenames()
		args[:0] = [self.Config['mediainfo']]
		subprocess.Popen(args,stdout=subprocess.PIPE)
