#!/usr/bin/python
# -*- coding: utf-8 -*-

import gtk, subprocess, os.path

from otrverwaltung.pluginsystem import Plugin
from otrverwaltung.GeneratorTask import GeneratorTask

from otrverwaltung.constants import Section

class Details(Plugin):
    Name = "Details"
    Desc = "Zeigt zu einer Video-Datei Details wie den verwendeten Codec und die Dauer an."
    Author = "Benjamin Elbers"
    Configurable = False
 
    def enable(self):
        treeselection = self.gui.main_window.builder.get_object('treeview_files').get_selection()
        self.on_treeselection_changed_id = treeselection.connect('changed', lambda callback: self.update_details())
                
        # Typ
        # Aspect-Ratio ...
        # Video-Format ...
        # Dauer        ...        
        padding = 3,3
        table = gtk.Table(4, 2)
        self.label_filetype = gtk.Label('')
        self.label_aspect = gtk.Label('...')
        self.label_video_format = gtk.Label('...')
        self.label_length = gtk.Label('...')
        
        table.attach(self.label_filetype, 0, 2, 0, 1, gtk.FILL, gtk.FILL, *padding)        
        table.attach(gtk.Label("Aspect-Ratio"), 0, 1, 1, 2, gtk.FILL, gtk.FILL, *padding)
        table.attach(self.label_aspect, 1, 2, 1, 2, gtk.FILL, gtk.FILL, *padding)
        table.attach(gtk.Label("Video-Format"), 0, 1, 2, 3, gtk.FILL, gtk.FILL, *padding)
        table.attach(self.label_video_format, 1, 2, 2, 3, gtk.FILL, gtk.FILL, *padding)
        table.attach(gtk.Label("Dauer"), 0, 1, 3, 4, gtk.FILL, gtk.FILL, *padding)
        table.attach(self.label_length, 1, 2, 3, 4, gtk.FILL, gtk.FILL, *padding)
        table.show_all()
        
        # add to bottom bar
        self.page_index = self.gui.main_window.builder.get_object('notebook_bottom').append_page(table, gtk.Label("Details"))
        
    def disable(self):                
        treeselection = self.gui.main_window.builder.get_object('treeview_files').get_selection()
        treeselection.disconnect(self.on_treeselection_changed_id)
    
        self.gui.main_window.builder.get_object('notebook_bottom').remove_page(self.page_index)
                      
    def update_details(self):       
        try:
            self.task.stop()
        except:
            pass
    
        if self.app.section == Section.PLANNING:
            self.reset_details("")
            return

        mplayer = self.app.config.get('mplayer')

        if not mplayer:
            self.reset_details("Der MPlayer ist nicht installiert!")
            return
      
        filenames = self.gui.main_window.get_selected_filenames()   
      
        if len(filenames) == 0:
            self.reset_details("<b>Keine Datei markiert.</b>")
        
        elif len(filenames) > 1:
            self.reset_details("<b>%s Dateien markiert.</b>" % len(filenames))
        
        else:
            filename = filenames[0]
           
            extension = os.path.splitext(filename)[1]
            
            self.label_filetype.set_markup("<b>%s-Datei</b>" % extension[1:])
            
            if extension != ".otrkey":

                def get_information():
                    yield
                                
                    # prettify the output!
                    def prettify_aspect(aspect):
                        if aspect == "1.7778":
                            return "16:9" 
                        elif aspect == "1.3333":
                            return "4:3"
                        else:
                            return aspect
                    
                    def prettify_length(seconds):                       
                        hrs = float(seconds) / 3600       
                        leftover = float(seconds) % 3600
                        mins = leftover / 60
                        secs = leftover % 60
                           
                        return "%02d:%02d:%02d" % (hrs, mins, secs)
                    
                    values = (
                        ("ID_VIDEO_ASPECT", self.label_aspect, prettify_aspect),
                        ("ID_VIDEO_FORMAT", self.label_video_format, None),
                        ("ID_LENGTH", self.label_length, prettify_length)
                        )
                  
                    process = subprocess.Popen([mplayer, "-identify", "-vo", "null", "-frames", "1", "-nosound", filename], stdout=subprocess.PIPE)
                          
                    while process.poll() == None:                                          
                        line = process.stdout.readline().strip()

                        for value, widget, callback in values:
                            
                            if line.startswith(value):
                                # mplayer gives an output like this: ID_VIDEO_ASPECT=1.3333
                                value = line.split("=")[1]
                                
                                if callback:
                                    value = callback(value)
                                
                                widget.set_text(value)   
                                
                self.task = GeneratorTask(get_information)
                self.task.start()
                            
    def reset_details(self, filetype=""):
        self.label_filetype.set_markup(filetype)
        self.label_aspect.set_text("...")
        self.label_video_format.set_text("...")
        self.label_length.set_text("...")                                    
