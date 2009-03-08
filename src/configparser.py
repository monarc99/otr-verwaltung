#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import isfile
import ConfigParser
import datetime
import sys

from constants import Save_Email_Password, Cut_action

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
                    'use_archive':          int(self.__read_value('common', 'use_archive', 0))                    
                },
            'folders':               
                {
                    'new_otrkeys':          self.__read_value('folders', 'new_otrkeys', ''),
                    'uncut_avis':           self.__read_value('folders', 'uncut_avis', ''),
                    'cut_avis':             self.__read_value('folders', 'cut_avis', ''),
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
                    'avi':                  self.__read_value('cut', 'avi', ''),
                    'hq':                   self.__read_value('cut', 'hq', ''),
                    'mp4':                  self.__read_value('cut', 'mp4', ''),
                    'man_avi':              self.__read_value('cut', 'man_avi', ''),
                    'man_hq':               self.__read_value('cut', 'man_hq', ''),
                    'man_mp4':              self.__read_value('cut', 'man_mp4', ''),
                    'server':               self.__read_value('cut', 'server', 'http://cutlist.at/'),
                    'cut_action':           int(self.__read_value('cut', 'cut_action', Cut_action.ASK)),
                    'delete_cutlists':      int(self.__read_value('cut', 'delete_cutlists', 1)),
                    'smart':                int(self.__read_value('cut', 'smart', 1))
                },
            'play':
                {
                    'player':               self.__read_value('play', 'player', ''),                    
                    'mplayer':              self.__read_value('play', 'mplayer', 'mplayer')
                },
            'planning':
                {
                    'planned_items':        self.__read_value('planning', 'planned_items', '')
                },
            'rename':
                {
                    'rename_cut':           int(self.__read_value('rename', 'rename_cut', 0)),
                    'schema':               self.__read_value('rename', 'schema', '{titel} vom {tag}. {MONAT} {jahr}, {stunde}:{minute} ({sender})'),            
                }
        }
               
        if config_dic['folders']['new_otrkeys'] != '' and config_dic['folders']['uncut_avis'] == '':
            config_dic['folders']['uncut_avis'] = config_dic['folders']['new_otrkeys']
        
        if config_dic['folders']['new_otrkeys'] != '' and config_dic['folders']['cut_avis'] == '':
            config_dic['folders']['cut_avis'] = config_dic['folders']['new_otrkeys']
        
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
