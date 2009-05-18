#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64

class Binding:
    def __init__(self, config, option, encode=False):      
        self.config = config        
        self.config.connect(option, self.on_config_changed)
        self.encode = encode
        
    def on_config_changed(self, value):
        # change gui
        pass        
        
class EntryBinding(Binding):

    def __init__(self, config, option, entry, encode=False):
        Binding.__init__(self, config, option, encode)
                
        self.entry = entry                
        self.entry.connect('changed', self.on_entry_changed, option)        
          
    def on_entry_changed(self, widget, option):
        if self.encode:
            self.config.set(option, base64.b64encode(widget.get_text()))
        else:               
            self.config.set(option, widget.get_text())
        
    def on_config_changed(self, value):        
        if self.encode:
            self.entry.set_text(base64.b64decode(value))
        else:               
            self.entry.set_text(value)
        
class CheckButtonBinding(Binding):

    def __init__(self, config, option, checkbutton):
        Binding.__init__(self, config, option)
                
        self.checkbutton = checkbutton                
        self.checkbutton.connect('toggled', self.on_check_toggled, option)        
          
    def on_check_toggled(self, widget, option):
        self.config.set(option, widget.get_active())
        
    def on_config_changed(self, value):        
        self.checkbutton.set_active(value)
        
class FileChooserBinding(Binding):

    def __init__(self, config, option, filechooser):
        Binding.__init__(self, config, option)
                
        self.filechooser = filechooser            
        self.filechooser.connect('current-folder-changed', self.on_folder_changed, option)        
          
    def on_folder_changed(self, widget, option):
        self.config.set(option, widget.get_filename())
        
    def on_config_changed(self, value):        
        self.filechooser.set_current_folder(value)
        
class ComboBoxEntryBinding(Binding):

    def __init__(self, config, option, comboboxentry):
        Binding.__init__(self, config, option)
                
        self.comboboxentry = comboboxentry             
        self.comboboxentry.child.connect('changed', self.on_entry_changed, option)        
          
    def on_entry_changed(self, widget, option):
        self.config.set(option, widget.get_text())
        
    def on_config_changed(self, value):        
        self.comboboxentry.child.set_text(value)
        
class RadioButtonsBinding(Binding):

    def __init__(self, config, option, radiobuttons):
        Binding.__init__(self, config, option)
                
        self.radiobuttons = radiobuttons
        for index, radiobutton in enumerate(self.radiobuttons):
            radiobutton.connect('toggled', self.on_radiobutton_toggled, option, index)        
          
    def on_radiobutton_toggled(self, widget, option, index):
        if widget.get_active():
            self.config.set(option, index)
        
    def on_config_changed(self, value):        
        self.radiobuttons[value].set_active(True)
