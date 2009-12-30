#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from otrverwaltung.gui.basewindow import BaseWindow
from otrverwaltung import path

class DialogPlugins(BaseWindow):
    
    def __init__(self, gui, parent):            
        self.gui = gui
    
        BaseWindow.__init__(self, "dialog_plugins", parent)
        
        self.get_widget('treeview_plugins').get_selection().connect('changed', self._on_selection_changed)
        
    def run(self):
        self.get_widget('liststore_plugins').clear()
    
        for name, plugin in self.gui.app.plugin_system.plugins.iteritems():
            enabled = (name in self.gui.app.plugin_system.enabled_plugins)
            self.get_widget('liststore_plugins').append([enabled, plugin.Name, plugin.Desc, name])
         
        if len(self.get_widget('liststore_plugins')) > 0:
            self.get_widget('treeview_plugins').get_selection().select_path((0,))
         
        self.get_window().run()
        self.hide()
        
    def _on_cellrenderer_enabled_toggled(self, widget, path, data=None):
        store = self.get_widget('liststore_plugins')
    
        iter = store.get_iter(path)
        store.set_value(iter, 0, not store.get_value(iter, 0))
        
        if store.get_value(iter, 0): # enable or disable plugin
            self.gui.app.plugin_system.enable(store.get_value(iter, 3))
        else:
            self.gui.app.plugin_system.disable(store.get_value(iter, 3))            
        
    def _on_selection_changed(self, selection, data=None):
        store, iter = selection.get_selected()       
        if not iter: return      
        
        self.get_widget('label_name').set_markup("<b>%s</b>" % store.get_value(iter, 1))
        self.get_widget('label_desc').set_markup("<b>Beschreibung: </b>\n%s" % store.get_value(iter, 2))
        name = store.get_value(iter, 3)
        self.get_widget('label_author').set_markup("<b>Autor: </b>\n%s" % self.gui.app.plugin_system.plugins[name].Author)
        self.get_widget('button_config').set_sensitive(self.gui.app.plugin_system.plugins[name].Configurable)
        
    def _on_button_config_clicked(self, widget, data=None):
        store, iter = self.get_widget('treeview_plugins').get_selection().get_selected()   
        name = store.get_value(iter, 3)       
        
        dialog = gtk.Dialog(store.get_value(iter, 1) + " - Einstellungen", parent=self.get_window(), flags=gtk.DIALOG_MODAL, buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        dialog.set_border_width(2)
        dialog.set_icon(gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('icon3.png')))
        
        dialog = self.gui.app.plugin_system.plugins[name].configurate(dialog)
        
        dialog.show_all()
        dialog.run()
        dialog.hide()
