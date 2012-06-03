#!/usr/bin/env python
# -*- coding: utf-8 -*-

from otrverwaltung.pluginsystem import Plugin
from otrverwaltung.constants import Section
import gtk, subprocess, os.path

class Mediainfo(Plugin):
	Name = "MediaInfo"
	Desc = "Analyse der Mediendatei"
	Author = "monarc99"
	Configurable = False

	def enable(self):
		self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('mediainfo.png')), 'MediaInfo', [Section.VIDEO_UNCUT, Section.VIDEO_CUT, Section.ARCHIVE, Section.TRASH])
		self.toolbutton.connect('clicked', self.mediainfo)

	def disable(self):
		self.gui.main_window.remove_toolbutton(self.toolbutton)

	def mediainfo(self, widget):
		""" Öffne die Datei mit mediainfo """

                args = self.gui.main_window.get_selected_filenames()
		args[:0] = ['mediainfo-gui']
		subprocess.Popen(args,stdout=subprocess.PIPE)
