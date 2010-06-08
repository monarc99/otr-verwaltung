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


import gobject
import gtk
import sys

class SidebarButton(gtk.Button):
    __gsignals__ = {
        'element-clicked' : (gobject.SIGNAL_RUN_FIRST, None, (int,))
    }
    
    def __init__(self, title, id, padding):
        gtk.Button.__init__(self)
        
        self.title = title
        self.active = False
        self.id = id
        self.search = None
 
        self.set_relief(gtk.RELIEF_NONE)  
        self.set_property('can_focus', False) # why?
 
        # HBox
        #   - [ Alignment(Label) | (image) ]

        self.box = gtk.HBox()

        a = gtk.Alignment(0.0, 0.5)
        a.set_property('left-padding', padding)
        
        self.label = gtk.Label()
        self.label.set_text(self.title)
        a.add(self.label)

        self.box.add(a)
        self.add(self.box)
        
        def on_clicked(button):
            self.emit('element-clicked', self.id)
                                
        self.connect('clicked', on_clicked)

    def add_widget(self, widget):
        self.box.pack_end(widget, expand=False)

    def update_text(self):
        if self.active:
            markup = '<b>%s</b>' % self.title
        else:
            markup = self.title
            
        if self.search is not None:
            markup += ' <b>(%i)</b>' % self.search
        
        self.label.set_markup(markup)

    def set_search(self, search):
        self.search = search
        self.update_text()

    def set_active(self, active_state):
        self.active = active_state
        self.update_text()        

class Sidebar(gtk.EventBox):
    __gsignals__ = {
        'element-clicked' : (gobject.SIGNAL_RUN_FIRST, None, (int,))
    }

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.set_size_request(200, -1)
        self.vbox = gtk.VBox()
        self.vbox.set_border_width(5)
        self.vbox.show()
        self.add(self.vbox)      

        self.elements = []

        style = self.get_style()
        self.color = gtk.gdk.color_parse('#AFAFAF')
        self.modify_bg(gtk.STATE_NORMAL, self.color)

    def on_element_clicked(self, element, id):
        self.set_active(id)
        self.emit('element-clicked', id)
    
    # public
    def set_active(self, id):                
        for element in self.elements:
            if id == element.id:
                element.set_active(True)
            else:
                element.set_active(False)
    
    def set_search(self, search_values):
        if search_values:
            for element in self.elements:
                key = element.id
                if key in search_values.keys():
                    element.set_search(search_values[key])
        else:
            for element in self.elements:
                element.set_search(None)
    
    def add_section(self, title):
        a = gtk.Alignment(0.0, 0.5)
        a.set_property('left-padding', 10)
        a.set_property('top-padding', 10)
        a.set_property('bottom-padding', 5)
        
        label = gtk.Label()
        label.set_markup('<span color="#6D6D6D"><b>%s</b></span>' % title)
        a.add(label)
        self.vbox.pack_start(a, False, False)      
    
    def add_element(self, id, title, intend=True):
        if intend:
            element = SidebarButton(title, id, 20)
        else:
            element = SidebarButton(title, id, 10)
            
        self.elements.append(element)
        element.connect('element-clicked', self.on_element_clicked)
        self.vbox.pack_start(element, False, False)
        
        return element
