#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import basename

import gtk

from basewindow import BaseWindow

class DialogRename(BaseWindow):
    
    def __init__(self, parent):            
        BaseWindow.__init__(self, "dialog_rename", parent)
        
    def init_and_run(self, title, filenames):        
        entries = {}
        for f in filenames:
            entries[f] = gtk.Entry()
            entries[f].set_text(basename(f))
            entries[f].set_activates_default(True)
            entries[f].show()
            self.get_widget('vboxRename').pack_start(entries[f])
        
        self.get_window().set_title(title)    
        response = self.run()        
        self.hide()
            
        # get new names
        new_names = {}
        for f in filenames:
            new_names[f] = entries[f].get_text()
          
        # remove entry widgets
        for f in entries:
            self.get_widget('vboxRename').remove(entries[f])
            
        return response==gtk.RESPONSE_OK, new_names
