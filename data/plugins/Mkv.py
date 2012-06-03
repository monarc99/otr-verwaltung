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

import gtk
import subprocess
import time
import os.path
import re

from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung.pluginsystem import Plugin
from otrverwaltung import fileoperations

from otrverwaltung.constants import Section

class Mkv(Plugin):
    Name = "MKV"
    Desc = "Wandelt avi-Dateien mit Hilfe von mkvmerge in mkv-Dateien um."
    Author = "Benjamin Elbers, monarc99"
    Configurable = True
    Config = { 'mkvmerge': 'mkvmerge',
	       'MkvNoHeaderCompression': True,
	       'DumpAVIs': True,
               'avidemux2_cli': 'avidemux2_cli',
               'EncodeAudioToAAC': False }
        
    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('mkv.png')), 'In Mkv umwandeln', [Section.VIDEO_CUT, Section.ARCHIVE])
        self.toolbutton.connect('clicked', self.on_mkv_clicked)                        
        
    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)
    
    def configurate(self, dialog):
        dialog.vbox.set_spacing(4) 
        
        dialog.vbox.pack_start(gtk.Label("Aufrufname von mkvmerge:"), expand=False)

        entry_mkvmerge = gtk.Entry()
        dialog.vbox.pack_start(entry_mkvmerge, expand=False)
        def on_entry_mkvmerge_changed(widget, data=None):
            self.Config['mkvmerge'] = widget.get_text()
        entry_mkvmerge.connect('changed', on_entry_mkvmerge_changed)

        # avidemux2cli config
        dialog.vbox.pack_start(gtk.Label("Aufrufname von avidemux2_cli:"), expand=False)
        entry_avidemux2_cli = gtk.Entry()
        dialog.vbox.pack_start(entry_avidemux2_cli, expand=False)
        def on_entry_avidemux2_cli_changed(widget, data=None):
            self.Config['avidemux2_cli'] = widget.get_text()
        entry_avidemux2_cli.connect('changed', on_entry_avidemux2_cli_changed)

	# checkbutton callback
        def on_checkbutton_toggled(widget, data=None):
            self.Config[data] = widget.get_active()

	# checkbutton for mkvcompression
	checkbutton_no_mkv_compression = gtk.CheckButton("MKV Header Kompression abschalten?")
        dialog.vbox.pack_start(checkbutton_no_mkv_compression, expand=False)
        checkbutton_no_mkv_compression.connect('toggled', on_checkbutton_toggled,'MkvNoHeaderCompression')

	# checkbutton for dumping avis
	checkbutton_dump_avis = gtk.CheckButton("AVIs automatisch in Mülleimer verschieben?")
        dialog.vbox.pack_start(checkbutton_dump_avis, expand=False)
        checkbutton_dump_avis.connect('toggled', on_checkbutton_toggled,'DumpAVIs')

	# checkbutton encode audio aac
	checkbutton_encode_audio = gtk.CheckButton("Audio zu AAC umwandeln?")
        dialog.vbox.pack_start(checkbutton_encode_audio, expand=False)
        checkbutton_encode_audio.connect('toggled', on_checkbutton_toggled,'EncodeAudioToAAC')

        # current config
        entry_mkvmerge.set_text(self.Config['mkvmerge'])
        entry_avidemux2_cli.set_text(self.Config['avidemux2_cli'])
        checkbutton_no_mkv_compression.set_active(self.Config['MkvNoHeaderCompression'])
        checkbutton_dump_avis.set_active(self.Config['DumpAVIs'])
        checkbutton_encode_audio.set_active(self.Config['EncodeAudioToAAC'])

        return dialog

    def on_mkv_clicked(self, widget, data=None):
        filenames = self.gui.main_window.get_selected_filenames()

        if len(filenames) == 0:
            self.gui.message_error_box("Es muss eine Datei markiert sein.")
            return

        self.toolbutton.set_sensitive(False)
        self.gui.main_window.set_tasks_visible(True)
        self.success = 0
        self.errors ={}
                
        def mkvmerge():
            for count, filename in enumerate(filenames):

                # avidemux2_cli pass
                if self.Config['EncodeAudioToAAC']:
                    yield 0, count
                    yield 3, 0
                    self.progress = 0
                    args = [self.Config['avidemux2_cli'], "--nogui", "--audio-codec", "AAC", "--load", filename, "--autoindex", "--force-b-frame", "--force-alt-h264", "--audio-map", "--audio-bitrate", "192", "--save", os.path.splitext(filename)[0] + "_AAC.avi"]
                    p = subprocess.Popen(args, stderr=subprocess.PIPE)

                    line = ""
                    infos_match = re.compile(r"Done:(\d{1,})%")

                    while p.poll() == None:
	                line = p.stderr.read(40)
	                m = re.search(infos_match,line)
	                if m:
                            yield 1, count
	                    yield 3, int(m.group(1))
                        else:
                            pass
                    exit_code = p.poll()

                    if exit_code == 0:
                        pass
                    else:
                        error = p.stderr.readline()
                        try:
                            error = error.split(":")[1]
                        except IndexError:
                            pass
                        if "unknown type" in error:
                            error = "Datei konnte nicht gelesen werden."
                        self.errors[filename] = error
                        continue

                # mkvmerge pass
                yield 2, count
                self.progress = 0
                outfile = fileoperations.make_unique_filename(os.path.splitext(filename)[0] + ".mkv")

                if self.Config['EncodeAudioToAAC']:
                    args = [self.Config['mkvmerge'], "-o", outfile, os.path.splitext(filename)[0] + "_AAC.avi"]
                else:
                    args = [self.Config['mkvmerge'], "-o", outfile, filename]

                if self.Config['MkvNoHeaderCompression']:
		  args[1:1] = ['--compression', '0:none', '--compression', '1:none']
                p = subprocess.Popen(args, stdout=subprocess.PIPE)
                p.stdout.readline()

                line = ""                            
                while p.poll() == None:
                    # read progress from stdout 
                    char = p.stdout.read(1)
                    line += char
                    progress = ''
                    if char == ':':
                        if "Error" in line or "Warning" in line:                            
                            break
                    
                        while char != '%':
                            char = p.stdout.read(1)
                            progress += char
                      
                        try:
                            self.progress = int(progress.strip(' %'))
                            yield 3, self.progress
                        except ValueError:
                            pass
                
                exit_code = p.poll()

                if exit_code == 0 or exit_code == 1:
                    self.success += 1
                    if self.Config['EncodeAudioToAAC']:
                        fileoperations.remove_file(os.path.splitext(filename)[0] + "_AAC.avi")
		    if self.Config['DumpAVIs']:
                        new_filename = os.path.join(self.app.config.get('general', 'folder_trash_avis'), os.path.basename(filename))
                        if os.path.exists(new_filename):
                            fileoperations.remove_file(new_filename)
			fileoperations.move_file(filename, self.app.config.get('general', 'folder_trash_avis'))
                else:
                    error = p.stdout.readline()
                    try:
                        error = error.split(":")[1]
                    except IndexError:
                        pass
                        
                    if "unknown type" in error:
                        error = "Datei konnte nicht gelesen werden."
                    self.errors[filename] = error
                  
        def loop(state, argument):            
            if state == 0:
                self.gui.main_window.set_tasks_text("Analysiere Datei ... %s/%s" % (str(argument + 1), str(len(filenames))))
            elif state == 1:
                self.gui.main_window.set_tasks_text("Audiospur in AAC wandeln ... %s/%s" % (str(argument + 1), str(len(filenames))))
            elif state == 2:
                self.gui.main_window.set_tasks_text("MKV erstellen ...  %s/%s" % (str(argument + 1), str(len(filenames))))
            else:                
                self.gui.main_window.set_tasks_progress(argument)
        
        def complete():
            if len(self.errors) == 0:
                self.gui.main_window.change_status(0, "Erfolgreich %s/%s Dateien umgewandelt." % (str(self.success), str(len(filenames))))
            else:
                self.gui.main_window.change_status(0, "Erfolgreich %s/%s Dateien umgewandelt. (Fehler: %s)" % (str(self.success), str(len(filenames)), " ".join(self.errors.values())))
            
            self.gui.main_window.set_tasks_visible(False)                
            if self.success > 0:
                self.app.show_section(self.app.section)
            self.toolbutton.set_sensitive(True)
                        
        GeneratorTask(mkvmerge, loop, complete).start() 
