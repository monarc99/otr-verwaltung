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

import xml.dom.minidom
import urllib
import ConfigParser
import os.path
import httplib

from otrverwaltung import fileoperations

class Cutlist:
    
    def __init__(self):
    
        # cutlist.at xml-output
        self.id = 0
        self.author = ''
        self.ratingbyauthor = 0
        self.rating = 0
        self.ratingcount = 0
        self.countcuts = 0        # !!! 
        self.actualcontent = ''
        self.usercomment = ''
        self.filename = ''
        self.withframes = 0
        self.withtime = 0
        self.duration = ''
        self.errors = ''
        self.othererrordescription = ''
        self.downloadcount = 0
        self.autoname = ''
        self.filename_original = ''

        # additions in cutlist file
        self.wrong_content = 0
        self.missing_beginning = 0
        self.missing_ending = 0
        self.other_error = 0
        self.suggested_filename = ''
        self.intended_app = ''
        self.intended_version = ''
        self.smart = 0
        self.fps = 0

        # own additions
        self.app = 'OTR-Verwaltung++'
        self.errors = False
        self.cuts_seconds = [] # (start, duration) list
        self.cuts_frames = [] # (start, duration) list
        self.local_filename = None
        
  
    def upload(self, server, cutlist_hash):
        """ Uploads a cutlist to cutlist.at "
            Upload code from:  http://code.activestate.com/recipes/146306/ 
            
            Returns: error message, otherwise None """
       
        boundary = '----------ThIs_Is_tHe_bouNdaRY_$'

        lines = [
            '--' + boundary,
            'Content-Disposition: form-data; name="userid"',
            '',
            cutlist_hash,
            '--' + boundary,
            'Content-Disposition: form-data; name="userfile[]"; filename="%s"' % self.local_filename,
            '',
            open(self.local_filename, 'r').read(),
            '--' + boundary + '--',
            '']

        body = '\r\n'.join(lines)

        connection = httplib.HTTPConnection(server.split('/')[2], 80)        
        headers = { 'Content-Type': 'multipart/form-data; boundary=%s' % boundary }

        try:
            connection.request('POST', server + "", body, headers)
        except Exception, error_message:
           return error_message       

        response = connection.getresponse().read()
        if 'erfolgreich' in response:
            return None
        else:
            return response

    def download(self, server, video_filename):
        """ Downloads a cutlist to the folder where video_filename is. 
            Checks whether cutlist already exists.
            
            Returns: error message, otherwise None """
        
        self.local_filename = video_filename
        count = 0
        
        while os.path.exists(self.local_filename + ".cutlist"):
            count += 1
            self.local_filename = "%s.%s" % (video_filename, str(count))
        
        self.local_filename += ".cutlist"
        
        # download cutlist
        url = server + "getfile.php?id=" + str(self.id)
        
        try:        
            self.local_filename, headers = urllib.urlretrieve(url, self.local_filename)
        except IOError, error:
            return "Cutlist konnte nicht heruntergeladen werden (%s)." % error
    
    def _check_string(self, string):
        try:
            res = string.decode('latin1').encode('utf-8')
        except:
            print "No latin1 string, trying utf-8"
            try:
                res = string.decode('utf-8').encode('utf-8')
            except:
                print "Malformed string"
                res = ""
        
        return res
    
    def read_from_file(self):
        config_parser = ConfigParser.SafeConfigParser()
        
        try:
            config_parser.read(self.local_filename)
            
            self.filename = self._check_string(config_parser.get('Info', 'SuggestedMovieName'))
            self.author = self._check_string(config_parser.get('Info', 'Author'))
            self.ratingbyauthor = int(config_parser.get('Info', 'RatingByAuthor'))
            self.rating = 0
            self.ratingcount = 0
            self.usercomment = self._check_string(config_parser.get('Info', 'UserComment'))
            self.countcuts = int(config_parser.get('General', 'NoOfCuts'))
            self.actualcontent = self._check_string(config_parser.get('Info', 'ActualContent'))
            self.filename_original = self._check_string(config_parser.get('General', 'ApplyToFile'))
        except:
            print "Malformed cutlist: ", self.local_filename
      
    def read_cuts(self):
        """ Reads cuts from local_filename.
            
            Returns: error message, otherwise None """
                    
        if self.cuts_seconds or self.cuts_frames:
            return
        
        config_parser = ConfigParser.SafeConfigParser()        
         
        try:            
            config_parser.read(self.local_filename)
        except ConfigParser.ParsingError, message:
            print "Malformed cutlist: ", message

        try:
            noofcuts = int(config_parser.get("General", "NoOfCuts"))
            
            for count in range(noofcuts):
                cut = "Cut" + str(count)
            
                if config_parser.has_option(cut, "StartFrame") and config_parser.has_option(cut, "DurationFrames"):
                    start_frame = int(config_parser.get(cut, "StartFrame"))
                    duration_frames = int(config_parser.get(cut, "DurationFrames"))
                    if duration_frames > 0:
                        self.cuts_frames.append((start_frame, duration_frames))                    
                        print "Append frames: %i, %i" % (start_frame, duration_frames)
                                    
                start_second = float(config_parser.get(cut, "Start"))
                duration_seconds = float(config_parser.get(cut, "Duration"))
                if duration_seconds > 0:
                    self.cuts_seconds.append((start_second, duration_seconds))     
                    print "Append seconds: %f, %f" % (start_second, duration_seconds)                                             

        except ConfigParser.NoSectionError, message:
            return "Fehler in Cutlist: " + str(message)
        except ConfigParser.NoOptionError, message:
            return "Fehler in Cutlist: " + str(message)
                
    def rate(self, rating, server):
        """ Rates a cutlist. 
            
            Returns: True for success."""
            
        url = "%srate.php?rate=%s&rating=%s" % (server, self.id, rating)

        try:
            print "[Cutlist] Rate URL:", url
            message = urllib.urlopen(url).read()
            print "[Cutlist] Rate message: ", message        
            
            if "Cutlist wurde bewertet. Vielen Dank!" in message:
                return True, message
            else:
                return False, message
        except IOError:
            return False, "Keine Internetverbindung"

    def write_local_cutlist(self, uncut_video, intended_app_name, my_rating):
        """ Writes a cutlist file to the instance's local_filename. """
    
        try:                        
            cutlist = open(self.local_filename, 'w')
                                        
            cutlist.writelines([
                "[General]\n",
                "Application=%s\n" % self.app,
                "Version=%s\n" % self.intended_version,
                "comment1=The following parts of the movie will be kept, the rest will be cut out.\n",
                "ApplyToFile=%s\n" % os.path.basename(uncut_video),
                "OriginalFileSizeBytes=%s\n" % str(fileoperations.get_size(uncut_video)),
                "FramesPerSecond=%s\n" % str(self.fps),
                "IntendedCutApplicationName=%s\n" % intended_app_name,
                "IntendedCutApplication=%s\n" % self.intended_app,
                "IntendedCutApplicationVersion=\n",
                "VDUseSmartRendering=%s\n" % str(int(self.smart)),
                "VDSmartRenderingCodecFourCC=0x53444646\n",
                "VDSmartRenderingCodecVersion=0x00000000\n",
                "NoOfCuts=%s\n" % str(len(self.cuts_frames)),
                "comment2=All values are given in seconds.\n",
                "\n",
                "[Info]\n",
                "Author=%s\n" % self.author,
                "RatingByAuthor=%s\n" % str(self.ratingbyauthor),
                "EPGError=%s\n" % str(int(self.wrong_content)),
                "ActualContent=%s\n" % str(self.actualcontent),
                "MissingBeginning=%s\n" % str(int(self.missing_beginning)),
                "MissingEnding=%s\n" % str(int(self.missing_ending)),
                "MissingVideo=0\n",
                "MissingAudio=0\n",
                "OtherError=%s\n" % str(int(self.other_error)),
                "OtherErrorDescription=%s\n" % str(self.othererrordescription),
                "SuggestedMovieName=%s\n" % str(self.suggested_filename),
                "UserComment=%s\n" % str(self.usercomment),
                "\n"
            ])
                      
            for count, (start_frame, duration_frames) in enumerate(self.cuts_frames):
                cutlist.writelines([
                    "[Cut%i]\n" % count,
                    "Start=%f\n" % (start_frame / self.fps),
                    "StartFrame=%i\n" % start_frame,             
                    "Duration=%f\n" % (duration_frames / self.fps),       
                    "DurationFrames=%i\n" % duration_frames,
                    "\n"
                ])
                                                    
        except IOError:
            print "Konnte Cutlist-Datei nicht erstellen: " + filename            
        finally:
            cutlist.close()

#
#
# Other methods
#
#
#

def download_cutlists(filename, server, choose_cutlists_by, cutlist_mp4_as_hq, error_cb=None, cutlist_found_cb=None):    
    """ Downloads all cutlists for the given file. 
            filename            - movie filename
            server              - cutlist server
            choose_cutlists_by  - 0 by size, 1 by name
            cutlist_mp4_as_hq   - 
            error_cb            - callback: an error occurs (message)
            cutlist_found_cb    - callback: a cutlist is found (Cutlist instance)
        
        Returns: error, a list of Cutlist instances    
    """

    if choose_cutlists_by == 0: # by size
        size = fileoperations.get_size(filename)
        urls = ["%sgetxml.php?ofsb=%s" % (server, str(size)),
                # siehe http://www.otrforum.com/showthread.php?t=59666
                "%sgetxml.php?ofsb=%s" % (server, str((size+2*1024**3)%(4*1024**3)- 2*1024**3))]
    
    else: # by name
        if "/" in filename:
            root, extension = os.path.splitext(os.path.basename(filename))
        else:
            root = filename
       
        if cutlist_mp4_as_hq and extension == '.mp4':
            root += ".HQ"
    
        urls = ["%sgetxml.php?name=%s" % (server, root)]

    cutlists = []
    
    for url in urls:
        print "[Cutlists] Download by : %s" % url
        try:
            handle = urllib.urlopen(url)
        except IOError:  
            if error_cb: error_cb("Verbindungsprobleme")
            return "Verbindungsprobleme", None
                       
        try:
            dom_cutlists = xml.dom.minidom.parse(handle)
            handle.close()
            dom_cutlists = dom_cutlists.getElementsByTagName('cutlist')
        except:
            if error_cb: error_cb("Keine Cutlists gefunden")
            return "Keine Cutlists gefunden", None
            
        for cutlist in dom_cutlists:
                                                                                   
            c = Cutlist()

            c.id                        = __read_value(cutlist, "id")
            c.author                    = __read_value(cutlist, "author")
            c.ratingbyauthor            = __read_value(cutlist, "ratingbyauthor")
            c.rating                    = __read_value(cutlist, "rating")
            c.ratingcount               = __read_value(cutlist, "ratingcount")
            c.countcuts                 = __read_value(cutlist, "cuts")
            c.actualcontent             = __read_value(cutlist, "actualcontent")
            c.usercomment               = __read_value(cutlist, "usercomment")
            c.filename                  = __read_value(cutlist, "filename")
            c.withframes                = __read_value(cutlist, "withframes")
            c.withtime                  = __read_value(cutlist, "withtime")
            c.duration                  = __read_value(cutlist, "duration")
            c.errors                    = __read_value(cutlist, "errors")
            c.othererrordescription     = __read_value(cutlist, "othererrordescription")
            c.downloadcount             = __read_value(cutlist, "downloadcount")
            c.autoname                  = __read_value(cutlist, "autoname")
            c.filename_original         = __read_value(cutlist, "filename_original")

            ids = [cutlist.id for cutlist in cutlists]
            if not c.id in ids:
                if cutlist_found_cb: cutlist_found_cb(c)
                   
                cutlists.append(c)

    if len(cutlists) == 0:
        return "Keine Cutlists gefunden", None
    else:
        return None, cutlists
        
def __read_value(cutlist_element, node_name):
    try:
        elements = cutlist_element.getElementsByTagName(node_name)
        for node in elements[0].childNodes:
            return node.nodeValue
    except:
        return ''
        
    return ''

def get_best_cutlist(cutlists):
    # Der Algorithmus berücksichtigt die Anzahl der Wertungen.
    # Hat eine Cutlist nur wenige Wertungen erhalten, wird 
    # ihre Bewertung etwas heruntergestuft. Existiert auch eine
    # andere Cutlist, die sehr viel mehr Wertungen erhalten hat, 
    # wird auf diese Weise auch diese Cutlist als beste genommen.
    #
    # Beispiel: Cutlist A: 
    #               Wertung: 5.00,  Anzahl der Bewerter: 2
    #           Cutlist B:
    #               Wertung: 4.88   Anzahl der Bewerter: 24
    #
    # Der Algorithmus sucht (im Gegensatz zu cutlist.at) Cutlist B
    # als beste heraus. 
    # Sind keine Benutzerwertungen vorhanden, wird nach der Autoren-
    # bewertung sortiert.

    best_cutlists = {}

    for cutlist in cutlists:
        if cutlist.rating:
            if int(cutlist.ratingcount) > 6:
                rating = float(cutlist.rating)
            else:
                rating = float(cutlist.rating) - (6 - int(cutlist.ratingcount)) * 0.05

            best_cutlists[cutlist] = rating

    if best_cutlists:
        items = best_cutlists.items()
    else:
        items = [(cutlist, cutlist.ratingbyauthor) for cutlist in cutlists]

    items.sort(lambda x,y: cmp(y[1], x[1]))

    return items[0][0]
