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

try: import simplejson as json
except ImportError: import json
import os.path

from otrverwaltung import path

class Config:
    """ Loads and saves configuration fields from/to file. """
    
    def __init__(self, config_file, fields):
        """ """        
        
        self.__config_file = config_file     
        self.__fields = fields   
        
        self.__callbacks = {}

    def connect(self, category, option, callback):
        self.__callbacks.setdefault(category, {})
        self.__callbacks[category].setdefault(option, []).append(callback)
          
    def set(self, category, option, value):            
        if option in ['email', 'password']:
            print "Set [%(category)s][%(option)s] to *****" % {"category": category, "option": option}   
        else:
            print "Set [%(category)s][%(option)s] to %(value)s" % {"category": category, "option": option, "value": value}   
            
        try:                       
            for callback in self.__callbacks[category][option]:
                callback(value)                
        except KeyError:
            pass
    
        self.__fields[category][option] = value        
  
    def get(self, category, option):
        """ Gets a configuration option. """      
        value = self.__fields[category][option]

        if option in ['email', 'password']:
            print "Get [%(category)s][%(option)s]: *****" % {"category": category, "option": option}
        else:
            print "Get [%(category)s][%(option)s]: %(value)s" % {"category": category, "option": option, "value": value}
       
        return value
          
    def save(self):
        """ Saves configuration to disk. """
                               
        try:
            # make sure directories exist
            try:
                os.makedirs(os.path.dirname(self.__config_file))
            except OSError:
                pass
            
            config_file = open(self.__config_file, "w")
            print _("Writing to "), config_file            
            json.dump(self.__fields, config_file, sort_keys=True, indent=4)
            config_file.close()
        except IOError, message:
            print _("Config file not available. Dumping configuration:")
            print json.dumps(self.__fields, sort_keys=True, indent=4)
       
    def load(self):
        """ Reads an existing configuration file. """
                       
        try:          
            config = open(self.__config_file, 'r')        
            json_config = json.load(config)
            config.close()
        except IOError, message:
            print _("Config file not available. Using default configuration.")
            json_config = {}
        
        for category, options in self.__fields.iteritems():
            for option, value in options.iteritems():
                try:
                    self.set(category, option, json_config[category][option])
                except KeyError:                
                    self.set(category, option, value)                     

    def get_program(self,  program):
        """ Returns the full calling string of a program 
            either the pure config value or the internal version, if the config value contains 'intern' """
        
        value = self.__fields['programs'][program]
        intern_program = path.get_tools_path(value)

        if 'intern-' in value:
            if os.path.isfile(intern_program):
                return intern_program
            
        return value
                
