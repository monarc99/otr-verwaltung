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

import gtk
from otrverwaltung.gui import AddDownloadDialog
from otrverwaltung.downloader import Download
import base64
import urllib
import hashlib
import os.path
import subprocess

from otrverwaltung.actions.baseaction import BaseAction
from otrverwaltung.GeneratorTask import GeneratorTask

def add_download(via_link, app, gui, link=None):
    if link:
        link = link.replace("otr://", "")

    dialog = AddDownloadDialog.NewAddDownloadDialog(gui, app.config, via_link, link)
        
    if dialog.run() == gtk.RESPONSE_OK:           
        options = dialog.get_download_options()
        
        password = base64.b64decode(app.config.get('general', 'password')) 
        
        if options[0] == 'torrent':
            user_id = options[1]
            hash = hashlib.md5(password).hexdigest()
            url = 'http://81.95.11.2/xbt/xbt_torrent_create.php?filename=%s&userid=%s&mode=free&hash=%s' % (dialog.filename, user_id, hash)
                        
            def download_torrent(url, filename):
                try:
                    urllib.urlretrieve(url, "/tmp/%s.torrent" % filename)
                    subprocess.call(['xdg-open', '/tmp/%s.torrent' % filename])
                except IOError, error:
                    yield "Torrentdatei konnte nicht heruntergeladen werden (%s)!" % error
                except OSError, error:
                    yield "Torrentdatei konnte nicht geöffnet werden (%s)!" % error

            def error(text):
                gui.main_window.change_status(-1, text)
        
            GeneratorTask(download_torrent, error).start(url, dialog.filename)

        else: # normal
            email = app.config.get('general', 'email')                
            cache_dir = app.config.get('general', 'folder_trash_otrkeys')
            decoder = app.config.get('general', 'decoder')
            
            if options[1] == 'decode':            
                download = Download(dialog.filename, link=options[2], output=app.config.get('general', 'folder_uncut_avis'))
                download.download_decode(decoder, cache_dir, email, password)
                                    
            elif options[1] == 'decodeandcut':
                cutlist = (app.config.get('general', 'server'), options[3]) # save server and id
                
                download = Download(dialog.filename, link=options[2], output=app.config.get('general', 'folder_cut_avis'))
                download.download_decode(decoder, cache_dir, email, password, cutlist)
                
            else:          
                download = Download(dialog.filename, link=options[1], output=app.config.get('general', 'folder_new_otrkeys'))
                preferred = app.config.get('downloader', 'preferred_downloader')
                if preferred != 'wget':
                    preferred = 'aria2c'                    

                download.download_basic(preferred, app.config.get('downloader', 'aria2c'), app.config.get('downloader', 'wget'))
                
            gui.main_window.treeview_download.add_objects(download)
            download.start() 
                                    
    dialog.destroy()
    
class Add(BaseAction):
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self):
        add_download(False, self.__app, self.__gui)
        
class AddLink(BaseAction):            
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self, link=None):
        add_download(True, self.__app, self.__gui, link)
        
class Stop(BaseAction):
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self, downloads):
        for download in downloads:
            download.stop()
        
class Start(BaseAction):
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self, downloads):
        for download in downloads:
            download.start()
