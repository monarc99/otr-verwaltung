#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, os.path, sys
import ConfigParser

import otrpath

class Plugin:  
    """ Basisklasse für Plugins """
     
    Name = "Name of Plugin"
    """ Name des Plugins """
    Desc = "Beschreibung"
    Author = "Autor"
    Configurable = False
    Config = { } # key-value-pairs for configuration
                 # just put your default values in here, the plugin system will do the rest for you
    
    def __init__(self, app, gui, dirname):
        """ Don't override the constructor. Do the intial work in 'enable'. """
        self.app = app       # for api access
        self.gui = gui       # for api access                
        self.dirname = dirname
    
    def enable(self):
        """ Diese Methode wird aufgerufen, wenn das Plugin aktiviert wird. """
        pass
        
    def disable(self):
        """ Diese Methode wird aufgerufen, wenn das Plugin deaktiviert wird.
            Es sollte alle in `enable` gemachten Änderungen rückgängig gemacht werden. """
        pass
        
    def configurate(self, dialog):
        """ Diese Methode wird aufgerufen, wenn der Benutzer das Plugin konfigurieren möchte.
            Alter the dialog.vbox property and return the dialog. The plugin system will do the rest.
            Remember to connect to the 'changed' signals of the widgets you placed in the dialog.
            Use the signals to update your Config dict.
            Note: Set CONFIGURABLE to True. """

        return dialog
    
    def get_path(self, file=None):
        
        if file:    
            return os.path.join(self.dirname, file)
        else:
            return self.dirname
                
class PluginSystem:
    
    def __init__(self, app, gui, conf_path, plugin_paths, enabled_plugins=''):
        self.plugins = {} # name : plugin instance
        self.enabled_plugins = [plugin for plugin in enabled_plugins.split(':') if plugin] # list of names
        self.conf_path = conf_path
       
        # read config
        print "[Plugins] Config path: ", conf_path
        self.parser = ConfigParser.ConfigParser()
        if os.path.isfile(conf_path):           
            self.parser.read(conf_path)            
       
        print "[Plugins] Paths to search: ", plugin_paths
                                     
        for path in plugin_paths:                  
            sys.path.append(path)           
            
            for file in os.listdir(path):
                plugin_name, extension = os.path.splitext(file)
                
                if extension == ".py":                        
                    plugin_module = __import__(plugin_name)
                    # instanciate plugin
                    
                    if not hasattr(plugin_module, plugin_name):
                        continue
                    
                    self.plugins[plugin_name] = getattr(plugin_module, plugin_name)(app, gui, os.path.dirname(plugin_module.__file__))
                    
                    config = {}
                    if self.parser.has_section(plugin_name):
                        for key, value in self.parser.items(plugin_name):
                            self.plugins[plugin_name].Config[key] = value
                    
                    print "[Plugins] Found: ", plugin_name
                        
        for plugin in self.enabled_plugins:
            if not plugin in self.plugins.keys():
                print "[Plugins] Error: Plugin >%s< not found." % plugin
                self.enabled_plugins.remove(plugin)                        
            else:
                self.plugins[plugin].enable()
                print "[Plugins] Enabled: ", plugin

    def enable(self, name):
        if name not in self.enabled_plugins:
            self.enabled_plugins.append(name)
        self.plugins[name].enable()
    
    def disable(self, name):
        self.enabled_plugins.remove(name)
        self.plugins[name].disable()
    
    def save_config(self):
        for plugin_name, plugin in self.plugins.iteritems():
            if not self.parser.has_section(plugin_name):
                self.parser.add_section(plugin_name)
            
            for option, value in plugin.Config.iteritems():                
                self.parser.set(plugin_name, option, value)
                print "[Plugins] Config (%s): set %s to %s" % (plugin_name, option, value)
                
        self.parser.write(open(self.conf_path, 'w'))
        
    def get_enabled_config(self):
        return ":".join(self.enabled_plugins)

