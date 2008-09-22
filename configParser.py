#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Author: Benjamin Elbers
#         elbersb@googlemail.com
#
#
# LICENSE: CREATIVE COMMONS
#          Attribution-Noncommercial-Share Alike 2.0 Generic
# http://creativecommons.org/licenses/by-nc-sa/2.0/
#

import ConfigParser
import os
import datetime
import sys

from constants import Action_after_decode, Action_after_cut, Save_Email_Password, Cut_action

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
                    'action_after_decode':  int(self.read_value('folders', 'action_after_decode', Action_after_decode.DELETE_OTRKEY)),
                    'decoded_otrkeys':      self.read_value('folders', 'decoded_otrkeys', ''),            
                    'action_after_cut':     int(self.read_value('folders', 'action_after_cut', Action_after_cut.DELETE_AVI)),
                    'cut_avis':             self.read_value('folders', 'cut_avis', ''),
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
