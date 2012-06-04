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

class MP4(Plugin):
    Name = "MP4"
    Desc = "Wandelt avi-Dateien in mp4-Dateien um."
    Author = "Benjamin Elbers, monarc99"
    Configurable = True
    Config = { 'mkvmerge': 'mkvmerge',
	       'MkvNoHeaderCompression': True,
	       'DumpAVIs': True,
               'EncodeAudioToAAC': True }
        
    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.image_new_from_file(self.get_path('mp4.png')), 'In MP4 umwandeln', [Section.VIDEO_CUT, Section.ARCHIVE])
        self.toolbutton.connect('clicked', self.on_mp4_clicked)                        
        
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

	# checkbutton callback
        def on_checkbutton_toggled(widget, data=None):
            self.Config[data] = widget.get_active()

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
        checkbutton_dump_avis.set_active(self.Config['DumpAVIs'])
        checkbutton_encode_audio.set_active(self.Config['EncodeAudioToAAC'])

        return dialog

    def __get_fps(self, filename):
        """ Gets the fps of a movie using mplayer. 
            Returns without error:              
                       fps, None
                    with error:
                       None, error_message """
        
        try:
            process = subprocess.Popen(["mplayer", "-vo", "null", "-msglevel", "all=6", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE)       
        except OSError:
            return None, "MPlayer wurde nicht gefunden!"            
        
        stdout = process.communicate()[0]
    
        for line in stdout.split('\n'):
            if "AVI video size" in line:
                frames = int(line[line.index("(")+1:line.index("audio")-2])
            elif "VIDEO:" in line:
                try:
                    return float(line[line.index("bpp")+3 : line.index("fps")]), frames
                except:
                    return None, "FPS konnte nicht bestimmt werden " + line
      
        return None, "FPS konnte nicht bestimmt werden."


    def on_mp4_clicked(self, widget, data=None):
        filenames = self.gui.main_window.get_selected_filenames()
        ffmpeg = self.get_path('ffmpeg.exe')

        if len(filenames) == 0:
        	self.gui.message_error_box("Es muss eine Datei markiert sein.")
        	return

        self.toolbutton.set_sensitive(False)
        self.gui.main_window.set_tasks_visible(True)
        self.success = 0
        self.errors ={}
                
        def mp4():
            for count, filename in enumerate(filenames):

                #fps bestimmen
                fps, max_frames = self.__get_fps(filename)
                if fps == None:
		    self.errors[filename] = max_frames
                    continue

                # mkvmerge pass
                yield 0, count
                self.progress = 0
                args = [self.Config['mkvmerge'], "-o", os.path.splitext(filename)[0] + "_remux.mkv", filename]

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
                            yield 4, self.progress                                
                        except ValueError:
                            pass
                
                exit_code = p.poll()

                if exit_code == 0 or exit_code == 1:
		    pass
		else:
                    error = p.stdout.readline()
                    if os.path.exists(os.path.splitext(filename)[0] + "_remux.mkv"):
                            fileoperations.remove_file(os.path.splitext(filename)[0] + "_remux.mkv")
                    try:
                        error = error.split(":")[1]
                    except IndexError:
                        pass
                        
                    if "unknown type" in error:
                        error = "Datei konnte nicht gelesen werden."
                    self.errors[filename] = error
                    continue

                # ffmpeg pass
                yield 1, count
                self.progress = 0
                new_filename = fileoperations.make_unique_filename(os.path.splitext(filename)[0] + "_remux.mp4")

                if self.Config['EncodeAudioToAAC']:
                    args = ["wine", ffmpeg, "-loglevel", "info", "-y", "-i", os.path.splitext(filename)[0] + "_remux.mkv", "-vcodec", "copy", "-aprofile", "aac_low", "-acodec", "aac", "-strict", "experimental", "-ab", "192k", "-cutoff", "18000", new_filename]
                else:
                    args = ["wine", ffmpeg, "-loglevel", "info", "-y", "-i", os.path.splitext(filename)[0] + "_remux.mkv", "-vcodec", "copy", "-acodec", "copy", new_filename]

                p = subprocess.Popen(args , stderr=subprocess.PIPE)

                yield 4, 0
                line = ""
                infos_match = re.compile(r"frame=\ {0,1}(\d{1,})")

                while p.poll() == None:
                    line = p.stderr.read(60)
                    print line
                    m = re.search(infos_match,line)
                    if m:
		        next = float( float(m.group(1)) / float(max_frames) ) * 100
		        if next > self.progress:
			    self.progress = next
			    yield 4, self.progress                                
                    else:
                        pass
                
                exit_code = p.poll()
                if os.path.exists(os.path.splitext(filename)[0] + "_remux.mkv"):
                            fileoperations.remove_file(os.path.splitext(filename)[0] + "_remux.mkv")

                if exit_code == 0:
		    pass
                else:
                    self.errors[filename] = "Fehler beim Erzeugen der MP4 Datei"
                    if os.path.exists(new_filename):
                        fileoperations.remove_file(new_filename)
                    continue

                #mp4box
                yield 2, count
                self.progress = 0
                outfile = fileoperations.make_unique_filename(os.path.splitext(filename)[0] + ".mp4")

                args = ["MP4Box", "-new", "-packed", "-fps", str(fps), "-add" , new_filename, outfile]
                p = subprocess.Popen(args , stdout=subprocess.PIPE)

                yield 4, 50
                while p.poll() == None:
		    time.sleep(1)
                    pass
                
                exit_code = p.poll()
                if os.path.exists(new_filename):
                            fileoperations.remove_file(new_filename)

                if exit_code == 0:
                    self.success += 1
		    if self.Config['DumpAVIs']:
		        yield 3, self.success
                        new_filename = os.path.join(self.app.config.get('general', 'folder_trash_avis'), os.path.basename(filename))
			fileoperations.move_file(filename, self.app.config.get('general', 'folder_trash_avis'))
                else:
                    self.errors[filename] = "Fehler beim Erzeugen der MP4 Datei"
                  
        def loop(state, argument):            
            if state == 0:
                self.gui.main_window.set_tasks_text("Extrahiere Streams aus AVI ... %s/%s" % (str(argument + 1), str(len(filenames))))
            elif state == 1:
                self.gui.main_window.set_tasks_text("MP4 erzeugen ... %s/%s" % (str(argument + 1), str(len(filenames))))
            elif state == 2:
                self.gui.main_window.set_tasks_text("MP4 optimieren ...  %s/%s" % (str(argument + 1), str(len(filenames))))
            elif state == 3:
                self.gui.main_window.set_tasks_text("Originaldatei in Mülleimer verschieben ...")
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
                        
        GeneratorTask(mp4, loop, complete).start() 
