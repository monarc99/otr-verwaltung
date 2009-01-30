#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from os.path import basename

import gtk

from basewindow import BaseWindow

class DialogRename(BaseWindow):
    
    def __init__(self, parent):
        widgets = [
            'vboxRename'
            ]
        
        builder = self.create_builder("dialog_rename.ui")
            
        BaseWindow.__init__(self, builder, "dialog_rename", widgets, parent)
        
    def init_and_run(self, title, filenames):        
        entries = {}
        for f in filenames:
            entries[f] = gtk.Entry()
            entries[f].set_text(basename(f))
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
