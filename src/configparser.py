#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, hashlib

from constants import Cut_action

class Config:
    def __init__(self, config_file):   
        self.__config_file = config_file
        self.__read()

    def get(self, option):
        """ Sets a configuration option. """       
        datatype, value = self.__config_dic[option]

        print "get config option %s: %s" % (option, value)
        
        return value
        
    def set(self, option, value):
        """ Sets a configuration option. """
        datatype, old_value = self.__config_dic[option]
        self.__config_dic[option] = datatype, value
        
        print "set config option %s to %s" % (option, value)

    def save(self):
        """ Saves configuration to disk. """
                                
        try:
            config = open(self.__config_file, "w")
        except IOError, message:
            print "Config file couldn't be written: ", message
            return
       
        # go through dictionary and save everything
        for key, (datatype, value) in self.__config_dic.iteritems():
            if datatype == bool:
                value = int(value)                
            
            config.write('%s=%s\n' % (key, str(value)))
               
        config.close()
        
    def __read(self):
        """ Reads an existing configuration file. """
                
        self.__config_dic = {
            'use_archive':          (bool, False),
            'show_details':         (bool, False),
            'folder_new_otrkeys':   (str, ''),
            'folder_uncut_avis':    (str, ''),
            'folder_cut_avis':      (str, ''),
            'folder_trash':         (str, ''),
            'folder_archive':       (str, ''),
            'decoder':              (str, ''),
            'save_email_password':  (bool, False),
            'email':                (str, ''),
            'password':             (str, ''),
            'verify_decoded':       (bool, False),          
            'cut_avis_by':          (str, ''),
            'cut_hqs_by':           (str, ''),
            'cut_mp4s_by':          (str, ''),
            'cut_avis_man_by':      (str, ''),
            'cut_hqs_man_by':       (str, ''),
            'cut_mp4s_man_by':      (str, ''),
            'server':               (str, 'http://cutlist.at/'),
            'cut_action':           (int, Cut_action.ASK),
            'delete_cutlists':      (bool, True),
            'smart':                (bool, True),
            'choose_cutlists_by':   (int, 0), # 0 = size, 1=name
            'cutlist_username':     (str, ''),
            'cutlist_hash':         (str, hashlib.md5(str(time.time())).hexdigest()[0:20]),
            'player':               (str, ''),
            'mplayer':              (str, ''),
            'planned_items':        (str, ''),
            'rename_cut':           (bool, False),
            'rename_schema':        (str, '{titel} vom {tag}. {MONAT} {jahr}, {stunde}:{minute} ({sender})')
        }
        
        try:           
            config = open(self.__config_file, 'r')
        except IOError, message:
            print "Config file couldn't be read: ", message
            
        # read file
        for line in config:
            if '=' in line:
                key, value = line.split('=', 1)
                key, value = key.strip(), value.strip()
                
                if key in self.__config_dic.keys():
                    datatype = self.__config_dic[key][0]
                    
                    #print "%5s: %15s=%15s" % (datatype, key.strip(), value)
                    if datatype == bool:
                        value = int(value)                    
                    
                    self.__config_dic[key.strip()] = datatype, datatype(value)
