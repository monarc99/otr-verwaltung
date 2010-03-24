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

import base64

class Config:
    def __init__(self, config_file, config_dic):  
        self.__config_file = config_file
        self.on_changed = {}
       
        self.__config_dic = config_dic

    def connect(self, option, callback):        
        if option not in self.on_changed.keys():
            self.on_changed[option] = []            
        self.on_changed[option].append(callback)
   
    def get(self, option):
        """ Sets a configuration option. """      
        datatype, value = self.__config_dic[option]

        if option in ['email', 'password']:
            print "[Config] Get config option %s" % option
        else:
            print "[Config] Get config option %s: %s" % (option, value)
       
        return value
       
    def set(self, option, value):
        """ Sets a configuration option. """
        datatype, old_value = self.__config_dic[option]
        self.__config_dic[option] = datatype, value
       
        if old_value == value:
            return
       
        if option in self.on_changed.keys():
            for method in self.on_changed[option]:
                method(value)
       
        if option in ['email', 'password']:
            value = "*****"
            
        print "[Config] Set config option %s to %s" % (option, value)

    def save(self):
        """ Saves configuration to disk. """
                               
        try:
            config = open(self.__config_file, "w")
        except IOError, message:
            print "Config file couldn't be written: ", message
            return
       
        # go through dictionary and save everything
        for key, (datatype, value) in self.__config_dic.iteritems():
            if datatype == bool:
                value = int(value)                
           
            config.write('%s=%s\n' % (key, str(value)))
               
        config.close()
       
    def read(self):
        """ Reads an existing configuration file. """
                       
        try:          
            config = open(self.__config_file, 'r')
        except IOError, message:
            print "Config file couldn't be read: ", message            
            return
           
        # read file
        for line in config:
            if '=' in line:
                key, value = line.split('=', 1)
                key, value = key.strip(), value.strip()
               
                if key in self.__config_dic.keys():
                    datatype = self.__config_dic[key][0]
                   
                    #print "%5s: %15s=%15s" % (datatype, key.strip(), value)
                    if datatype == bool:                     
                        value = bool(int(value))
                   
                    option = key.strip()
                    value = datatype(value)
                    self.__config_dic[option] = datatype, value
       
                    if option in self.on_changed.keys():
                        for method in self.on_changed[option]:
                            method(value)


class Binding:
    def __init__(self, config, option, encode=False):      
        self.config = config        
        self.config.connect(option, self.on_config_changed)
        self.encode = encode
        self.on_config_changed(config.get(option))
        
    def on_config_changed(self, value):
        # change gui
        pass        
        
class EntryBinding(Binding):

    def __init__(self, config, option, entry, encode=False):
        self.entry = entry                
        self.entry.connect('changed', self.on_entry_changed, option)  
    
        Binding.__init__(self, config, option, encode)               
            
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
        self.checkbutton = checkbutton                
        self.checkbutton.connect('toggled', self.on_check_toggled, option)     
    
        Binding.__init__(self, config, option)               
            
    def on_check_toggled(self, widget, option):
        self.config.set(option, widget.get_active())
        
    def on_config_changed(self, value):        
        self.checkbutton.set_active(value)
        
class FileChooserBinding(Binding):

    def __init__(self, config, option, filechooser):                
        self.filechooser = filechooser            
        self.filechooser.connect('current-folder-changed', self.on_folder_changed, option)        
        
        Binding.__init__(self, config, option)
            
    def on_folder_changed(self, widget, option):
        self.config.set(option, widget.get_filename())
        
    def on_config_changed(self, value):        
        self.filechooser.set_current_folder(value)
        
class ComboBoxEntryBinding(Binding):

    def __init__(self, config, option, comboboxentry):
        self.comboboxentry = comboboxentry             
        self.comboboxentry.child.connect('changed', self.on_entry_changed, option)  
    
        Binding.__init__(self, config, option)      
            
    def on_entry_changed(self, widget, option):
        self.config.set(option, widget.get_text())
        
    def on_config_changed(self, value):        
        self.comboboxentry.child.set_text(value)
        
class RadioButtonsBinding(Binding):

    def __init__(self, config, option, radiobuttons):     
        self.radiobuttons = radiobuttons
        for index, radiobutton in enumerate(self.radiobuttons):
            radiobutton.connect('toggled', self.on_radiobutton_toggled, option, index)        
            
        Binding.__init__(self, config, option)            
            
    def on_radiobutton_toggled(self, widget, option, index):
        if widget.get_active():
            self.config.set(option, index)
        
    def on_config_changed(self, value):        
        self.radiobuttons[value].set_active(True)                                 
