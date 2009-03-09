#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.dom.minidom
import urllib
import ConfigParser

import fileoperations

def download_cutlists(filename, server, error_cb=None, cutlist_found_cb=None):    
    size = fileoperations.get_size(filename)
    url = "%sgetxml.php?version=0.9.8.0&ofsb=%s" % (server, str(size))
      
    try:
        handle = urllib.urlopen(url)
    except IOError:  
        if error_cb: 
            error_cb("Verbindungsprobleme")
        return []
                   
    try:
        dom_cutlists = xml.dom.minidom.parse(handle)
        handle.close()
        dom_cutlists = dom_cutlists.getElementsByTagName('cutlist')
    except:
        if error_cb: 
            error_cb("Keine Cutlists gefunden")
        return []
                    
    cutlists = []           
        
    for cutlist in dom_cutlists:
                                                                        
        cutlist_data = [
           __read_value(cutlist, "id"),
           __read_value(cutlist, "author"),
           __read_value(cutlist, "ratingbyauthor"),
           __read_value(cutlist, "rating"),
           __read_value(cutlist, "ratingcount"),
           __read_value(cutlist, "cuts"),
           __read_value(cutlist, "actualcontent"),
           __read_value(cutlist, "usercomment"),
           __read_value(cutlist, "filename"),
           __read_value(cutlist, "withframes"),
           __read_value(cutlist, "withtime"),
           __read_value(cutlist, "duration"),
           __read_value(cutlist, "errors"),
           __read_value(cutlist, "othererrordescription"),
           __read_value(cutlist, "downloadcount")]
                                   
        if cutlist_found_cb: 
            cutlist_found_cb(cutlist_data)
            
        cutlists.append(cutlist_data)

    return cutlists            

def __read_value(cutlist_element, node_name):
    value = None
    try:
        elements = cutlist_element.getElementsByTagName(node_name)
        for node in elements[0].childNodes:
            return node.nodeValue
    except:
        return ""
    
    if value == None:
        return ""               

def download_cutlist(cutlist_id, server, filename):
    # download cutlist
    url = server + "getfile.php?id=" + str(cutlist_id)
            
    filename, headers = urllib.urlretrieve(url, filename)
  
def get_cuts_of_cutlist(filename):    
    config_parser = ConfigParser.SafeConfigParser()        
    
    try:
        config_parser.read(filename)
    except ConfigParser.ParsingError:
        print "Malformed cutlist: ", error
    
    noofcuts = 0        
    cuts = []
    try:
        noofcuts = int(config_parser.get("General", "NoOfCuts"))
        
        for count in range(noofcuts):
            cuts.append((count,
                         float(config_parser.get("Cut" + str(count), "Start")), 
                         float(config_parser.get("Cut" + str(count), "Duration"))))            

    except ConfigParser.NoSectionError, message:
        return "Fehler in Cutlist: " + str(message)
    except ConfigParser.NoOptionError, message:
        return "Fehler in Cutlist: " + str(message)
        
    return cuts
        
def get_best_cutlist(cutlists):
    dic_cutlists = {}
    
    for cutlist in cutlists:                          
        ratingbyauthor = cutlist[2]
        userrating = cutlist[3]
        ratingcount = cutlist[4]                            

        if ratingbyauthor == "":
            rating = userrating
        elif userrating == "":
            rating = ratingbyauthor
        else:
            rating = float(ratingbyauthor) * 0.3 + float(userrating) * 0.7

        dic_cutlists[cutlist[0]] = rating
    
    sort_cutlists = dic_cutlists.items()
    sort_cutlists.sort(key=lambda x: x[1], reverse=True) # first is the best
                    
    return sort_cutlists[0][0] # get first (=the best) cutlist; from the tuple, get the first (id) item
    
def rate(cutlist, rating, server):
    url = "%srate.php?version=0.9.8.0&rate=%s&rating=%s" % (server, cutlist, rating)

    try:
        urllib.urlopen(url)                                 
        return True
    except IOError, e:
        print e
        return False
