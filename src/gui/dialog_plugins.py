#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from basewindow import BaseWindow

class DialogPlugins(BaseWindow):
    
    def __init__(self, gui, parent):            
        self.gui = gui
    
        BaseWindow.__init__(self, "dialog_plugins", parent)
        
        self.get_widget('treeview_plugins').get_selection().connect('changed', self.on_selection_changed)
        
    def run(self):
        self.get_widget('liststore_plugins').clear()
    
        for name, plugin in self.gui.app.plugin_system.plugins.iteritems():
            enabled = (name in self.gui.app.plugin_system.enabled_plugins)
            self.get_widget('liststore_plugins').append([enabled, plugin.Name, plugin.Desc, name])
         
         
        self.get_window().run()
        self.hide()
        
    def on_cellrenderer_enabled_toggled(self, widget, path, data=None):
        store = self.get_widget('liststore_plugins')
    
        iter = store.get_iter(path)
        store.set_value(iter, 0, not store.get_value(iter, 0))
        
        if store.get_value(iter, 0): # enable or disable plugin
            self.gui.app.plugin_system.enable(store.get_value(iter, 3))
        else:
            self.gui.app.plugin_system.disable(store.get_value(iter, 3))            
        
    def on_selection_changed(self, selection, data=None):
        store, iter = selection.get_selected()       
        if not iter: return
        
        self.get_widget('label_name').set_markup("<b>%s</b>" % store.get_value(iter, 1))
        self.get_widget('label_desc').set_markup("<b>Beschreibung: </b> %s" % store.get_value(iter, 2))
        name = store.get_value(iter, 3)
        self.get_widget('label_author').set_markup("<b>Autor: </b> %s" % self.gui.app.plugin_system.plugins[name].Author)
        self.get_widget('button_config').set_sensitive(self.gui.app.plugin_system.plugins[name].Configurable)
        
    def on_button_config_clicked(self, widget, data=None):
        store, iter = self.get_widget('treeview_plugins').get_selection().get_selected()   
        name = store.get_value(iter, 3)        
        self.gui.app.plugin_system.plugins[name].configurate()
