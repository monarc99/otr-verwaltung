#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.dom.minidom
import urllib
import ConfigParser
import os.path
import httplib

import fileoperations

def upload_cutlist(filename, userid):
    # http://code.activestate.com/recipes/146306/

    boundary = '----------ThIs_Is_tHe_bouNdaRY_$'

    lines = [
        '--' + boundary,
        'Content-Disposition: form-data; name="userid"',
        '',
        'userid',
        '--' + boundary,
        'Content-Disposition: form-data; name="userfile[]"; filename="%s"' % filename,
        '',
        open(filename, 'r').read(),
        '--' + boundary + '--',
        ''
    ]

    body = '\r\n'.join(lines)

    connection = httplib.HTTPConnection("www.cutlist.at", 80)
    
    headers = {
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary
    }

    try:
        connection.request('POST', "/index.php?upload=2", body, headers)
    except Exception, error_message:
       return error_message  
    
    response = connection.getresponse()

    response_content =  response.read()

    if 'erfolgreich' in response_content:
        return None

def download_cutlists(filename, server, choose_cutlists_by, error_cb=None, cutlist_found_cb=None):    
    size = fileoperations.get_size(filename)

    if choose_cutlists_by == 0: # by size
        url = "%sgetxml.php?ofsb=%s" % (server, str(size))
    else: # by name
        url = "%sgetxml.php?name=%s" % (server, os.path.basename(filename))
      
    print url
        
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
           __read_value(cutlist, "downloadcount"),
           __read_value(cutlist, "autoname"),
           __read_value(cutlist, "filename_original")
           ]
                                   
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

def download_cutlist(cutlist_id, server, avi_filename):
    """ Downloads a cutlist to the folder where avi_filename is. 
        Checks whether cutlist already exists.
        Returns a tuple:
            local filename of cutlist, error message. """
    
    local_filename = avi_filename
    count = 0
    
    while os.path.exists(local_filename + ".cutlist"):
        count += 1
        local_filename = "%s.%s" % (avi_filename, str(count))
    
    local_filename += ".cutlist"
    
    # download cutlist
    url = server + "getfile.php?id=" + str(cutlist_id)
    
    try:        
        local_filename, headers = urllib.urlretrieve(url, local_filename)
    except IOError, error:
        return None, "Cutlist konnte nicht heruntergeladen werden (%s)." % error
        
    return local_filename, None
  
def get_cuts_of_cutlist(filename):    
    config_parser = ConfigParser.SafeConfigParser()        
    
    try:
        config_parser.read(filename)
    except ConfigParser.ParsingError, error:
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
                    
    return sort_cutlists[0] # get first (=the best) cutlist; from the tuple
    
def rate(cutlist, rating, server):
    url = "%srate.php?version=0.9.8.0&rate=%s&rating=%s" % (server, cutlist, rating)

    try:
        urllib.urlopen(url)                                 
        return True
    except IOError, e:
        print e
        return False
