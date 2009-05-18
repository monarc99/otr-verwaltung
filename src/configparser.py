#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Config:
    def __init__(self, config_file, config_dic):   
        self.__config_file = config_file
        self.on_changed = {}
        
        self.__config_dic = config_dic

    def connect(self, option, callback):        
        if option not in self.on_changed.keys():
            self.on_changed[option] = []            
        self.on_changed[option].append(callback)
    
    def get(self, option):
        """ Sets a configuration option. """       
        datatype, value = self.__config_dic[option]

        print "[Config] Get config option %s: %s" % (option, value)
        
        return value
        
    def set(self, option, value):
        """ Sets a configuration option. """
        datatype, old_value = self.__config_dic[option]
        self.__config_dic[option] = datatype, value
        
        if old_value == value:
            return
        
        if option in self.on_changed.keys():
            for method in self.on_changed[option]:
                method(value)
        
        print "[Config] Set config option %s to %s" % (option, value)

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
        
    def read(self):
        """ Reads an existing configuration file. """
                       
        try:           
            config = open(self.__config_file, 'r')
        except IOError, message:
            print "Config file couldn't be read: ", message            
            return
            
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
                    
                    option = key.strip()
                    value = datatype(value)
                    self.__config_dic[option] = datatype, value
        
                    if option in self.on_changed.keys():
                        for method in self.on_changed[option]:
                            method(value)
