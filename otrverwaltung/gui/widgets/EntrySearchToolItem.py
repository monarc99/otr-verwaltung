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


class EntrySearchToolItem(gtk.ToolItem):
    __gsignals__ = {
        'clear' : (gobject.SIGNAL_RUN_FIRST, None, ()),
        'search': (gobject.SIGNAL_RUN_FIRST, None, (str,))
    }
      
    def __init__(self, default_search_text):
        gtk.ToolItem.__init__(self)
        self.search_timeout = 0
        self.default_search_text = default_search_text

        self.entry = gtk.Entry()
        
        self.entry.set_text(self.default_search_text)
        self.entry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_CLEAR )
        self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
        
        self.entry.connect("focus-in-event", self.on_entry_focus_in)
        self.entry.connect("focus-out-event", self.on_entry_focus_out)        
        self.entry.connect("key-press-event", self.on_entry_key_pressed)
        self.entry.connect("icon-press", self.on_entry_icon_pressed)
        # Hold on to this id so we can block emission when initially clearing text
        self.change_handler_id = self.entry.connect("changed", self.on_entry_changed)       

        self.add(self.entry)
        self.show_all()

    def do_clear(self):
        print 'do_clear'
        self._clear_entry()

    def _clear_entry(self):
        """ Avoids sending 'changed' signal when clearing text. """
        self.entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.entry.handler_block(self.change_handler_id)
        self.entry.set_text("")
        self.entry.handler_unblock(self.change_handler_id)

    def _reset_entry(self):
        self.entry.handler_block(self.change_handler_id)    
        self.entry.set_text(self.default_search_text)
        self.entry.handler_unblock(self.change_handler_id)
        self.entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))            

    def on_entry_focus_in(self, widget, data):
        """ Clear default search text on focus. """        
        self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        if self.entry.get_text() == self.default_search_text:
            self._clear_entry()
            
    def on_entry_focus_out(self, widget, data):
        """ Set default text on focus out. """
        if not self.entry.get_text():
            self._reset_entry()
            
    def on_entry_icon_pressed(self, widget, icon_pos, event):
        self.emit("clear")        
            
    def _typing_timeout(self):
        if self.entry.get_text():
            self.emit("search", self.entry.get_text())
        self.search_timeout = 0
        return False

    def on_entry_changed(self, widget):
        if self.search_timeout != 0:
            gobject.source_remove(self.search_timeout)
            self.search_timeout = 0

        if len(self.entry.get_text()) == 0:            
            self.emit("clear")
        else:            
            self.entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#E8E7B6"))
            self.search_timeout = gobject.timeout_add(250, self._typing_timeout)

    def on_entry_key_pressed(self, w, ev):   
        """ Clear on escape. """
        if ev.keyval == gtk.gdk.keyval_from_name("Escape") and len(self.entry.get_text()) > 0:
            self.emit("clear")
            return True
