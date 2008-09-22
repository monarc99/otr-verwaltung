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

import ConfigParser
import os
import datetime
import sys

from constants import Save_Email_Password, Cut_action

class Config:
    def __init__(self):
        # a new ConfigParser
        self.config_parser = ConfigParser.ConfigParser()

    def read(self, config_file):
        """ read config file, if exists, otherwise, use default value """
        
        try:
            if os.path.isfile(config_file):
                self.config_parser.read(config_file)
        except Exception, inst:
            print "Config file couldn't be read: "
            print "ERROR: ", inst
            sys.exit(-1)  
         
        # create config dictionary to return
        config_dic = {
            'common':
                {
                    'activate_cut':         int(self.read_value('common', 'activate_cut', 1)),
                    'use_archive':          int(self.read_value('common', 'use_archive', 0)),                   
                        
                },
            'folders':               
                {
                    'new_otrkeys':          self.read_value('folders', 'new_otrkeys', ''),                    
                    'trash':                self.read_value('folders', 'trash', ''),
                    'archive':              self.read_value('folders', 'archive', '')
                },
            'decode':
                {
                    'path':                 self.read_value('decode', 'path', ''),
                    'save_email_password':  int(self.read_value('decode', 'save_email_password', Save_Email_Password.DONT_SAVE)),
                    'email':                self.read_value('decode', 'email', ''),
                    'password':             self.read_value('decode', 'password', ''),
                    'correct':              int(self.read_value('decode', 'correct', 0))              
                },
            'cut':
                {
                    'avidemux':             self.read_value('cut', 'avidemux', ''),
                    'server':               self.read_value('cut', 'server', 'http://cutlist.de'),
                    'cut_action':           int(self.read_value('cut', 'cut_action', Cut_action.ASK))
                },
            'play':
                {
                    'player':               self.read_value('play', 'player', ''),
                    'use_cut_play':         int(self.read_value('play', 'use_cut_play', 0)),
                    'mplayer':              self.read_value('play', 'mplayer', 'mplayer')
                }
        }
        
        # return the dictionary
        return config_dic
   
    def save(self, config_file, config_dic):
        """ Called by app to save the config dictionary.
            Creates a new config file if it doesn't exist """
        try:
            if os.path.isfile(config_file):
                f = open(config_file, "w")
            else:
                print "Config file %s does not exist, creating a new one..." % config_file
                f = open(config_file, "w")                   
        except Exception, inst:
            print "Config file couldn't be read: "
            print "ERROR: ", inst
            sys.exit(-1)  
       
        # go through dictionary and save everything
        for section in config_dic:
            for option in config_dic[section]:
                self.save_value(section, option, config_dic[section][option])
                
        self.config_parser.write(f)
        
        f.close()
        
    def read_value(self, section, option, default):
        """ Reads values from the ConfigParser object. If the
            file doesn't exist or is corrupt, use the default
            value """        
        try:
            value = self.config_parser.get(section, option)
        except ConfigParser.NoSectionError:
            value = default
        except ConfigParser.NoOptionError:
            value = default
        
        return value
    
    def save_value(self, section, option, value):
        """ Saves values to ConfigParser.
            Creates sections and options if they don't exist. """
        try:
            self.config_parser.set(section, option, value)
        except ConfigParser.NoSectionError:
            # if the section doesn't exist, create it and 
            # call the method again
            self.config_parser.add_section(section)
            self.save_value(section, option, value)
