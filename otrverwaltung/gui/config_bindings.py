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

class ConfigBinding:
    def __init__(self, widget, config, category, option):
        self.widget = widget
        self.config = config
        self.category = category
        self.option = option

        # set intial state
        self.change_value(config.get(category, option))
        # add callback if config option changed
        self.config.connect(category, option, self.change_value)
    
    def change_value(value):
        raise NotImplementedError("This method should be overridden.")

class CheckButtonBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)
        
        # add signal
        self.widget.connect('toggled', self.on_toggled)
    
    def change_value(self, value):
        self.widget.set_active(value)
        
    def on_toggled(self, widget, data=None):
        self.config.set(self.category, self.option, self.widget.get_active())  
        
class EntryBinding(ConfigBinding):
    def __init__(self, widget, config, category, option, encode=False):
        self.encode = encode
        ConfigBinding.__init__(self, widget, config, category, option)
                
        # add signal
        self.widget.connect('changed', self.on_changed)
    
    def change_value(self, value):
        if self.encode:
            self.widget.set_text(base64.b64decode(value))
        else:
            self.widget.set_text(value)
        
    def on_changed(self, widget, data=None):
        if self.encode:
            self.config.set(self.category, self.option, base64.b64encode(self.widget.get_text()))
        else:
            self.config.set(self.category, self.option, self.widget.get_text())           

class FileChooserFolderBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)

        # add signal
        self.widget.connect('current-folder-changed', self.on_folder_changed)
        self.widget.connect('selection-changed', self.on_folder_changed)
    
    def change_value(self, value):
        if self.widget.get_filename() != value:
            self.widget.set_current_folder(value)
        
    def on_folder_changed(self, widget, data=None):
        self.config.set(self.category, self.option, self.widget.get_filename())    
        
class RadioButtonsBinding(ConfigBinding):
    def __init__(self, widgets, config, category, option):
        ConfigBinding.__init__(self, widgets, config, category, option)
        
        for index, radiobutton in enumerate(widgets):
            radiobutton.connect('toggled', self.on_toggled, index)
    
    def change_value(self, value):
        self.widget[value].set_active(True)
        
    def on_toggled(self, widget, index):
        if widget.get_active():
            self.config.set(self.category, self.option, index)
            
class ComboBoxEntryBinding(ConfigBinding):
    def __init__(self, widget, config, category, option):
        ConfigBinding.__init__(self, widget, config, category, option)
        
        self.widget.child.connect('changed', self.on_changed)  
    
    def change_value(self, value):
        self.widget.child.set_text(value)
        
    def on_changed(self, widget, data=None):
        self.config.set(self.category, self.option, widget.get_text())            
