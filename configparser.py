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

from os.path import isfile
import ConfigParser
import datetime
import sys

from constants import Save_Email_Password, Cut_action, On_Quit

class Config:
    def __init__(self, config_file):
        # a new ConfigParser
        self.__config_parser = ConfigParser.ConfigParser()        
        self.__config_file = config_file
        self.__config_dic = self.__read()

    def save(self):
        """ Called by app to save the config dictionary.
            Creates a new config file if it doesn't exist. """
                                
        try:
            f = open(self.__config_file, "w")
        except IOError, inst:
            print "Config file couldn't be written: "
            print "ERROR: ", inst
            return  
       
        # go through dictionary and save everything
        for section in self.__config_dic:
            for option in self.__config_dic[section]:
                self.__save_value(section, option, self.__config_dic[section][option])
        
        self.__config_parser.write(f)
        
        f.close()
        
    def get(self, section, option):
        """ Sets a configuration options """
        return self.__config_dic[section][option]
        
    def set(self, section, option, value):
        """ Updates configuration. """
        self.__config_dic[section][option] = value

    def __read(self):
        """ read config file, if exists, otherwise, use default value """
        
        if isfile(self.__config_file):
            try:           
                self.__config_parser.read(self.__config_file)
            except Exception, inst:
                print "Config file couldn't be read: "
                print "ERROR: ", inst
                print "... will start with default values ..."
                
         
        # create config dictionary to return
        config_dic = {
            'common':
                {
                    'activate_cut':         int(self.__read_value('common', 'activate_cut', 1)),
                    'use_archive':          int(self.__read_value('common', 'use_archive', 0)),        
                    'on_quit':             int(self.__read_value('common', 'on_quit', On_Quit.ASK))                       
                },
            'folders':               
                {
                    'new_otrkeys':          self.__read_value('folders', 'new_otrkeys', ''),                    
                    'trash':                self.__read_value('folders', 'trash', ''),
                    'archive':              self.__read_value('folders', 'archive', '')
                },
            'decode':
                {
                    'path':                 self.__read_value('decode', 'path', ''),
                    'save_email_password':  int(self.__read_value('decode', 'save_email_password', Save_Email_Password.DONT_SAVE)),
                    'email':                self.__read_value('decode', 'email', ''),
                    'password':             self.__read_value('decode', 'password', ''),
                    'correct':              int(self.__read_value('decode', 'correct', 0))              
                },
            'cut':
                {
                    'avidemux':             self.__read_value('cut', 'avidemux', ''),
                    'server':               self.__read_value('cut', 'server', 'http://cutlist.de'),
                    'cut_action':           int(self.__read_value('cut', 'cut_action', Cut_action.ASK))
                },
            'play':
                {
                    'player':               self.__read_value('play', 'player', ''),
                    'use_cut_play':         int(self.__read_value('play', 'use_cut_play', 0)),
                    'mplayer':              self.__read_value('play', 'mplayer', 'mplayer')
                }
        }
        
        return config_dic
      
    def __read_value(self, section, option, default):
        """ Reads values from the ConfigParser object. If the
            file doesn't exist or is corrupt, use the default
            value """        
        try:
            value = self.__config_parser.get(section, option)
        except ConfigParser.NoSectionError:
            value = default
        except ConfigParser.NoOptionError:
            value = default
        
        return value
    
    def __save_value(self, section, option, value):
        """ Saves values to ConfigParser.
            Creates sections and options if they don't exist. """
        try:
            self.__config_parser.set(section, option, value)
        except ConfigParser.NoSectionError:
            # if the section doesn't exist, create it and 
            # call the method again
            self.__config_parser.add_section(section)
            self.__save_value(section, option, value)
