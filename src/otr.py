#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os.path import join, isdir, exists
import re
import subprocess
import time
import hashlib

try:
    from gtk import events_pending, main_iteration
    from gtk import gdk
    import gobject
    gdk.threads_init()    
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

if exists(join(sys.path[0], 'otrpath.py')):    
    LOCAL = True
else:
    LOCAL = False
    sys.path.insert(0, "/usr/share/otr-verwaltung")
    
# intern
from gui.gui import Gui
from pluginsystem import PluginSystem
from actions import actions
from configparser import Config
import fileoperations
import cutlists as cutlists_management
from constants import Section, Action, Cut_action
from planning import Planning
import otrpath

class App:
    """ Hauptklasse des Programms. """
    
    section = Section.OTRKEY
    """ Die aktuell angezeigt `~constants.Section`. Zum Ändern sollte die Funktion `~otr.App.show_section` verwendet werden. """
    
    def __init__(self):     
        config_dic = {
            'folder_new_otrkeys':   (str, ''),
            'folder_uncut_avis':    (str, ''),
            'folder_cut_avis':      (str, ''),
            'folder_trash':         (str, ''),
            'folder_archive':       (str, ''),
            'player':               (str, ''),
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
            'player':               (str, ''),
            'mplayer':              (str, ''),
            'planned_items':        (str, ''),
            'rename_cut':           (bool, False),
            'rename_schema':        (str, '{titel} vom {tag}. {MONAT} {jahr}, {stunde}-{minute} ({sender})'),
            'cutlist_mp4_as_hq':    (bool, False), # for mp4s, when searching cutlist by name, add an HQ --> Name.HQ.mp4
            'show_bottom':          (bool, False),
            'enabled_plugins':      (str, 'Play'),
            'cutlist_hash':         (str, hashlib.md5(str(time.time())).hexdigest()),
            'window_settings':      (str, '')
        }
                   
        # read configs
        if LOCAL:
            print "[Config] Path: ", otrpath.get_path('conf')
            self.config = Config(otrpath.get_path('conf'), config_dic)
        else:
            print "[Config] Path: ", otrpath.get_config_path('conf')
            self.config = Config(otrpath.get_config_path('conf'), config_dic)
        self.config.read()                

        self.__search_text = ""
        self.locked = False
            
        # regex
        self.uncut_video = re.compile('.*_([0-9]{2}\.){2}([0-9]){2}_([0-9]){2}-([0-9]){2}_.*_([0-9])*_TVOON_DE.mpg\.(avi|HQ\.avi|mp4)$')
        self.cut_video = re.compile('.*(avi|mp4|mkv|wmv)$')
       
        # load gui
        self.__gui = Gui(self)
        self.__gui.preferences_window.update_config_values()
    
        if self.config.get('window_settings'):
            maximize, width, height = self.config.get('window_settings').split(',')
            if int(maximize):
                self.__gui.main_window.get_window().maximize()            
            self.__gui.main_window.get_window().resize(int(width), int(height))
    
        # load plugins
        if LOCAL:
            plugin_paths = [otrpath.get_path('plugins')]
            pluginconf_path = otrpath.get_path('pluginconf')
        else:
            plugin_paths = otrpath.get_plugin_paths()
            pluginconf_path = otrpath.get_config_path('pluginconf')
    
        self.plugin_system = PluginSystem(self, self.__gui, pluginconf_path, plugin_paths, self.config.get('enabled_plugins'))
    
        # show undecoded otrkeys         
        self.show_section(Section.OTRKEY)
        
        self.planned_broadcasts = Planning()
        self.planned_broadcasts.read_config(self.config.get('planned_items'))
        
        self.__gui.main_window.broadcasts_badge()                           
             
    ### 
    ### Show sections
    ###
    
    def show_section(self, section):
        """ Zeigt eine der verschiedenen `Sections <constants.Section>` an. 
                        
            * aktualisiert einen Treeview und zeigt den korrekten an
            * setzt die aktuelle `~otr.App.section`
            * zeigt die korrekten Toolbuttons an """

        # set current section
        self.section = section
        
        # set toolbar
        self.__gui.main_window.set_toolbar(section)
                
        self.__gui.main_window.clear_files()
        files = []
        text = ""
        
        if section == Section.PLANNING:
            text = self.__section_planning()
      
            self.__gui.main_window.show_planning(True)
        else:
            self.__gui.main_window.show_planning(False)
        
        if section == Section.OTRKEY:
            text, files = self.__section_otrkey()
        
        elif section == Section.VIDEO_UNCUT:
            text, files = self.__section_video_uncut()   

        elif section == Section.VIDEO_CUT:
            text, files = self.__section_video_cut()   

        elif section == Section.TRASH:
            text, files = self.__section_trash()   

        elif section == Section.ARCHIVE: 
            # returns NO files       
            text = self.__section_archive()

        if len(files) > 0: # this is not executed when the section is "Archive"
            if len(files) == 1:
                text += " (1 Datei)"
            else:
                text += " (%s Dateien) " % len(files)
            
            files.sort() 
            
            # put filenames into treestore
            for f in files:
                # TODO: don't show files if in use
                self.__append_row_treeview_files(None, f)

        # set message text
        self.__gui.main_window.get_widget('labelMessage').set_markup(text)


    # helper for different sections
    def __section_planning(self):
        text = "Diese Aufnahmen wurden geplant." 
       
        for count, broadcast in enumerate(self.planned_broadcasts):
            if self.search(broadcast.title):
                self.__gui.main_window.append_row_planning(self.planned_broadcasts[count])
            
        return text
             
    def __section_otrkey(self):
        text = "Diese Dateien wurden noch nicht dekodiert." 
        path = self.config.get('folder_new_otrkeys')
        
        if path == "":
            return text, []
        
        files = [join(path, f) for f in os.listdir(path) if f.endswith(".otrkey") and self.search(f)]                           
            
        return (text, files)
         
    def __section_video_uncut(self):
        text = "Diese Dateien wurden noch nicht geschnitten."
        path = self.config.get('folder_uncut_avis')
        
        files = [join(path, f) for f in os.listdir(path) if self.uncut_video.match(f) and self.search(f)]
            
        return (text, files)
        
    def __section_video_cut(self):
        text = "Diese Video-Dateien sind fertig geschnitten. Sie können ins Archiv verschoben werden."
                
        path = self.config.get('folder_cut_avis')
        
        files = []                
        for f in os.listdir(path):
            if not self.uncut_video.match(f):
                if self.cut_video.match(f):
                    if self.search(f):
                        files += [join(path, f)]
        
        return (text, files)
        
    def __section_trash(self):
        text = "Diese otrkey- und Video-Dateien wurden bereits dekodiert bzw. geschnitten. Sie können normalerweise gelöscht werden."
        path = self.config.get('folder_trash')
                    
        files = [join(path, f) for f in os.listdir(path) if (f.endswith('.otrkey') or self.cut_video.match(f)) and self.search(f)]
                
        return (text, files)

    def __section_archive(self):
        text = "Diese Dateien wurden ins Archiv verschoben."

        path = self.config.get('folder_archive')
        
        self.__tree(None, path)        
        
        return text            
                 
    # recursive function for archive to add folders and files with a tree structure
    def __tree(self, parent=None, path=None):              
        if parent != None:            
            dir = self.__gui.main_window.get_widget('treeview_files').get_model().get_value(parent, 0)
        else:  # base path (archive directory)
            dir = path

        files = []
        files = os.listdir(dir)            

        for file in files:
            full_path = join(dir, file)
            
            if isdir(full_path):                
                iter = self.__append_row_treeview_files(parent, full_path)
                self.__tree(iter)
            else:
                if self.cut_video.match(file):
                    if self.search(file):
                        self.__append_row_treeview_files(parent, full_path)

    ###
    ### Helpers
    ###
    
    def rename_by_schema(self, filename, schema=""):
        """ Gibt den nach dem angegebenen Schema umbenannten Dateinamen zurück. Wird `schema` leer gelassen, so wird das eingestellte Schema verwendet. """
    
        if schema == "":
            schema = self.config.get('rename_schema')        
        
        if self.uncut_video.match(filename):           
            
            parts = filename.split('_')
            parts.reverse()

            titel_list = parts[6:len(parts)]
            titel_list.reverse()
            titel = " ".join(titel_list)
            titel_mit = "_".join(titel_list)

            stunde, minute = parts[4].split('-')
            jahr, monat, tag = parts[5].split('.')           
            monatsname = time.strptime(monat, '%m')
            monatsname = time.strftime('%B', monatsname)

            sender_gross = parts[3].capitalize()

            format = parts[0]
            mp4 = False
            
            if 'mp4' in format:
                format = 'mp4'
            if 'HQ' in format:
                format = 'HQ'            
            else:
                format = 'avi'

            values = {
                'titel' : titel,
                'titel_' : titel_mit,
                'sender' : parts[3],
                'SENDER': sender_gross,
                'tag': tag,
                'monat': monat,
                'MONAT': monatsname,
                'jahr': jahr,
                'stunde': stunde,
                'minute': minute,
                'dauer' : parts[2],
                'format' : format
            }
             
            for token, value in values.iteritems():
                schema = schema.replace('{%s}' % token, value)                            
                
            return schema
        else:         
            return filename
     
    def __append_row_treeview_files(self, parent, filename):        
        iter = self.__gui.main_window.append_row_files(parent, filename, fileoperations.get_size(filename), fileoperations.get_date(filename))
        return iter
     
    
    ### 
    ### Search
    ### 
                      
    def start_search(self, search):
        """ #FIXME """

        self.__search_text = search.lower()

        items = []        
        # create dict of counts
        counts = {}

        for method, section in [(self.__section_otrkey, Section.OTRKEY),
                                (self.__section_video_uncut, Section.VIDEO_UNCUT),
                                (self.__section_video_cut, Section.VIDEO_CUT),
                                (self.__section_trash, Section.TRASH)]:
            files = []
            text, items = method()   
            count = len(items)
            if count > 0:
                counts[section] = "(%s)" % count
            else:
                counts[section] = ""
         
        # archive 
        files = []       
        for root, dirs, wfiles in os.walk(self.config.get('folder_archive')):
            for f in wfiles:                
                if self.cut_video.match(f) and self.search(f):
                    files += [join(root, f)]

        count = len(files)
        if count > 0:
            counts[Section.ARCHIVE] = "(%s)" % count
        else:
            counts[Section.ARCHIVE] = ""

        # planning
        items = []
        for count, broadcast in enumerate(self.planned_broadcasts):
            if self.search(broadcast.title):
                items += [count]

        count = len(items)
        if count > 0:
            counts[Section.PLANNING] = "(%s)" % count
        else:
            counts[Section.PLANNING] = ""
        
        self.show_section(self.section)                   
        
        return counts
    
    def stop_search(self):
        """ #FIXME """
        
        self.__search_text = ""
        self.show_section(self.section)
        
    def search(self, f):
        """ #FIXME """
        
        if self.__search_text == "":
            return True
        else:    
            if self.__search_text in f.lower():
                return True
            else:
                return False
        
    ###
    ### Actions
    ###        
    
    def perform_action(self, chosen_action, filenames=None, broadcasts=None, cut_action=None):
        """ #FIXME """
       
        if broadcasts != None and chosen_action in [Action.PLAN_EDIT, Action.PLAN_SEARCH, Action.PLAN_REMOVE, Action.PLAN_ADD, Action.PLAN_RSS]:
            if len(broadcasts) == 0 and not chosen_action in [Action.PLAN_ADD, Action.PLAN_RSS]:
                if len(self.__gui.main_window.get_widget('treeview_planning').get_model()) > 0:
                    if self.__gui.question_box("Es ist keine Sendung markiert! Sollen alle Sendungen verarbeitet werden?"):
                        broadcasts = []                    

                        def foreach(model, path, iter, broadcasts):
                            broadcasts += [iter]

                        self.__gui.main_window.get_widget('treeview_planning').get_model().foreach(foreach, broadcasts)
                    else:
                        return
                else:
                    return

        elif filenames != None:
            if len(filenames) == 0 and chosen_action != Action.NEW_FOLDER:
                if len(self.__gui.main_window.get_widget('treeview_files').get_model()) > 0:
                    if self.__gui.question_box("Es ist keine Datei markiert! Sollen alle Dateien verarbeitet werden?"):
                        filenames = [row[0] for row in self.__gui.main_window.get_widget('treeview_files').get_model()]
                    else:
                        return
                else:
                    return          

        action = actions.get_action(chosen_action, self.__gui)

        self.locked = True
               
        # different actions:
        if chosen_action in [Action.DECODE, Action.CUT, Action.DECODEANDCUT]:             
            action.do(chosen_action, filenames, self.config, self.rename_by_schema, cut_action)
    
        elif chosen_action == Action.RENAME: 
            action.do(filenames)
    
        elif chosen_action == Action.REAL_DELETE: 
            action.do(filenames)
    
        elif chosen_action == Action.RESTORE: 
            action.do(filenames, self.config.get('folder_new_otrkeys'), self.config.get('folder_uncut_avis'), self.config.get('folder_cut_avis'), self.uncut_video)
    
        elif chosen_action == Action.DELETE:
            action.do(filenames, self.config.get('folder_trash'))      

        elif chosen_action == Action.PLAN_REMOVE: 
            action.do(broadcasts, self.planned_broadcasts) 
    
        elif chosen_action == Action.PLAN_SEARCH: 
            action.do(broadcasts, self.planned_broadcasts)            
    
        elif chosen_action == Action.PLAN_ADD: 
            action.do(self.planned_broadcasts)
    
        elif chosen_action == Action.PLAN_EDIT: 
            action.do(broadcasts[0], self.planned_broadcasts)       
            
        elif chosen_action == Action.PLAN_RSS:
            action.do(self.planned_broadcasts, self.config.get('email'), self.config.get('password')) 
    
        elif chosen_action == Action.ARCHIVE: 
            action.do(filenames, self.config.get('folder_archive'))
     
        elif chosen_action == Action.NEW_FOLDER:
            if len(filenames) == 0:
                action.do(self.config.get('folder_archive'))
            else:
                action.do(filenames[0])
        
        self.locked = False
        
        # update view?
        if action.update_list:            
            self.__gui.main_window.do_search(self.__search_text)
            self.show_section(self.section)
            
    
    def play_file(self, filename):
        """ #FIXME """        
        
        subprocess.Popen(['xdg-open', filename])
    
    def __show(self, cuts, video_filename, edl_subtitles_cb):        
        f_edl = open(join(self.config.get('folder_new_otrkeys'), ".tmp.edl"), "w")
        f_sub = open(join(self.config.get('folder_new_otrkeys'), ".tmp.sub"), "w")    
        
        edl_subtitles_cb(f_edl, f_sub, cuts)        
        
        f_edl.close()
        f_sub.close()
        
        f_edl = join(self.config.get('folder_new_otrkeys'), ".tmp.edl")
        f_sub = join(self.config.get('folder_new_otrkeys'), ".tmp.sub")
            
        p = subprocess.Popen([self.config.get('mplayer'), "-osdlevel", "3", "-edl", f_edl, "-sub", f_sub, video_filename])
       
        # wait
        while p.poll() == None:
            time.sleep(1)
            while events_pending():
                main_iteration(False)
                
        fileoperations.remove_file(f_edl)
        fileoperations.remove_file(f_sub)
        
    def show_cuts(self, video_filename, cutlist):       
        """ #FIXME """
        
        def edl_subtitles_cb(f_edl, f_sub, cuts):            
            diff = 11
            pre_diff = 5
            
            sub_count = 0

            f_edl.write("0 ")      

            for count, start, duration in cuts:
                end = start + duration

                f_edl.write("%s 0\n" % (start - diff))
                f_edl.write("%s %s 0\n" % (start + pre_diff, end - diff))
                f_edl.write("%s " % (end + pre_diff))

                for second in range(diff):
                    sub_count += 1
                    f_sub.write("%s\n" % sub_count)
                    f_sub.write("%s --> %s\n" % (self.format_seconds(start-diff+second), self.format_seconds(start-diff+second+1)))
                    f_sub.write("Zum Schnitt noch %s Sekunden...\n\n" % str(diff - second))            
                    
                for second in range(diff):
                    sub_count += 1
                    f_sub.write("%s\n" % sub_count)
                    f_sub.write("%s --> %s\n" % (self.format_seconds(end-diff+second), self.format_seconds(end-diff+second+1)))
                    f_sub.write("Zum Schnitt noch %s Sekunden...\n\n" % str(diff - second))
                
            f_edl.write("50000 0")
         
        error = cutlist.read_cuts()
                
        if error:
            self.__gui.message_error_box(error)
            return           

        self.__show(cutlist.cuts, video_filename, edl_subtitles_cb)            
    
    def show_cuts_after_cut(self, video_filename, cutlist):
        """ #FIXME """
        
        def edl_subtitles_cb(f_edl, f_sub, cuts):                    
            diff = 11
            pre_diff = 5
                        
            length = 0
            sub_count = 0
                            
            for count, start, duration in cuts:
                f_edl.write("%s %s 0\n" % (pre_diff + length, length + duration - diff))
                length += duration
                
                # vor dem schnitt:
                for second in range(diff):
                    sub_count += 1
                    f_sub.write("%s\n" % sub_count)
                    f_sub.write("%s --> %s\n" % (self.format_seconds(length - diff + second), self.format_seconds(length - diff + second + 1)))
                    f_sub.write("Zum Schnitt noch %s Sekunden...\n\n" % str(diff - second))                      


        error = cutlist.read_cuts()
                
        if error:
            self.__gui.message_error_box(error)
            return           

        self.__show(cutlist.cuts, video_filename, edl_subtitles_cb)
    
    def format_seconds(self, seconds):
        """ #FIXME """
        
        hrs = seconds / 3600       
        leftover = seconds % 3600
        mins = leftover / 60
        secs = leftover % 60
        ms = int(seconds) - seconds
        
        return "%02d:%02d:%02d,%03d" % (hrs, mins, secs, ms)
                      
    def run(self):
        """ #FIXME """
        
        self.__gui.main_window.show()      
        

        if self.config.get('folder_new_otrkeys') == "":      
            self.__gui.message_info_box("Dies ist offenbar das erste Mal, dass OTR-Verwaltung gestartet wird.\n\nEs müssen zunächst einige wichtige Einstellungen vorgenommen werden. Klicken Sie dazu auf OK.")
            self.__gui.preferences_window.show()
               
        self.__gui.run()
        
        # write to config
        self.config.set('planned_items', self.planned_broadcasts.get_config())               
        self.config.set('enabled_plugins', self.plugin_system.get_enabled_config())
        

        maximized = str(int(self.__gui.main_window.maximized))
        width = str(self.__gui.main_window.size[0])
        height = str(self.__gui.main_window.size[1])
        
        settings = ','.join([maximized, width, height])
        self.config.set('window_settings', settings)
        
        # save plugins' configuration
        self.plugin_system.save_config()
 
if __name__ == '__main__':            
    app = App()
    app.run()
    app.config.save()
