#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import basename

import gtk

from otrverwaltung import path

class RenameDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "RenameDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)
        
    def init_and_run(self, title, filenames):        
        entries = {}
        for f in filenames:
            entries[f] = gtk.Entry()
            entries[f].set_text(basename(f))
            entries[f].set_activates_default(True)
            entries[f].show()
            self.builder.get_object('vboxRename').pack_start(entries[f])
        
        self.set_title(title)    
        response = self.run()        
        self.hide()
            
        # get new names
        new_names = {}
        for f in filenames:
            new_names[f] = entries[f].get_text()
          
        # remove entry widgets
        for f in entries:
            self.builder.get_object('vboxRename').remove(entries[f])
            
        return response==gtk.RESPONSE_OK, new_names
        
def NewRenameDialog():
    glade_filename = path.getdatapath('ui', 'RenameDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("rename_dialog")
        
    return dialog        
