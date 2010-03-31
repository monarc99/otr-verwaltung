# -*- coding: utf-8 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gtk
import urllib
import re

from otrverwaltung.GeneratorTask import GeneratorTask
from otrverwaltung import path

class AddDownloadDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "AddDownloadDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)

        animation = gtk.gdk.PixbufAnimation(path.get_image_path("spinner.gif"))
        self.builder.get_object('image_spinner').set_from_animation(animation)

        selection = self.builder.get_object('treeview_programs').get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect('changed', self.treeview_programs_selection_changed)
    
    def search(self, text):
        html = urllib.urlopen("http://otrkeyfinder.com/?search=%s" % text).read()
        results = re.findall(r'title="(([^&]*)_([0-9\.]*)_([0-9-]*)_([^_]*)_([0-9]*)_TVOON_DE.mpg\.(avi|HQ\.avi|HD\.avi|mp4).otrkey)"[^\(]*>\(([0-9]*)\)', html)
        for result in results:
            filename, name, date, time, station, length, format, mirrors = result
                        
            name = name.replace('_', ' ')
            date = "%s.%s.20%s" % tuple(reversed(date.split('.')))
            time = time.replace('-', ':')
            station = station.capitalize()
            length = "%s min" % length
            
            yield [filename, name, station, date, time, format, length, int(mirrors)]
                
    # signals #
    def treeview_programs_selection_changed(self, treeselection, data=None):
        model, iter = treeselection.get_selected()
        self.builder.get_object('button_ok').set_sensitive(iter!=None)
       
    def on_button_search_clicked(self, widget, data=None):
        text = self.builder.get_object('entry_search').get_text()
        if len(text) < 3:
            self.builder.get_object('label_status').set_markup("<b>Die Suche muss mindesten 3 Zeichen haben!</b>")
            return
        else:
            for char in text:
                if not char.lower() in 'abcdefghijklmnopqrstuvwxyz0123456789.-_ *':
                    self.builder.get_object('label_status').set_markup("<b>Erlaubt sind nur Groß- und Kleinbuchstaben, die Ziffern 0 bis 9, der Punkt, das Minus, der Unterstrich und der Stern/Leerzeichen als Platzhalter!</b>")
                    return
                        
            self.builder.get_object('label_status').set_markup("")
        
        model = self.builder.get_object('liststore_programs')
        model.clear()
        self.builder.get_object('scrolledwindow_programs').hide()
        self.builder.get_object('vbox_searching').show()
        self.builder.get_object('button_search').set_sensitive(False)
        
        def callback(row):
            model.append(row)
        
        def stop():
            self.builder.get_object('scrolledwindow_programs').show()                
            self.builder.get_object('vbox_searching').hide()
            self.builder.get_object('button_search').set_sensitive(True)
            self.builder.get_object('label_status').set_text("Es wurden %i Dateien gefunden!" % len(model))
        
        GeneratorTask(self.search, callback, stop).start(text)
    
    def on_treeview_programs_row_activated(self, treeview, path, view_column, data=None):
        iter = treeview.get_model().get_iter(path)
        self.forward(iter)
        
    def on_button_ok_clicked(self, widget, data=None):
        selection = self.builder.get_object('treeview_programs').get_selection()        
        model, iter = selection.get_selected()
        self.forward(iter)
        
    def forward(self, iter):
        filename, mirrors = self.builder.get_object('liststore_programs').get(iter, 0, 7)
        
        self.builder.get_object('scrolledwindow_programs').hide()
        self.builder.get_object('vbox_searching').show()
        self.builder.get_object('label_status').set_markup("")
        self.builder.get_object('button_search').set_sensitive(False)
        self.builder.get_object('label_searching_status').set_markup("<b>Informationen werden gesammelt...</b>")        
        print filename
        print mirrors

def NewAddDownloadDialog():
    glade_filename = path.getdatapath('ui', 'AddDownloadDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("add_download_dialog")
    return dialog
