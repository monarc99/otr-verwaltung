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

from otrverwaltung.actions.baseaction import BaseAction

def add_download(via_link, app, gui, link=None):
    if link:
        link = link.replace("otr://", "")

    dialog = AddDownloadDialog.NewAddDownloadDialog(gui, app.config, via_link, link)
        
    if dialog.run() == gtk.RESPONSE_OK:           
        options = dialog.get_download_options()
                
        if options[0] == 'torrent':
#            def download_torrent(url, filename):
#                try:
#                    urllib.urlretrieve(url, "/tmp/%s.torrent" % filename)
#                    subprocess.call(['xdg-open', '/tmp/%s.torrent' % filename])
#                except IOError, error:
#                    yield "Torrentdatei konnte nicht heruntergeladen werden (%s)!" % error
#                except OSError, error:
#                    yield "Torrentdatei konnte nicht geöffnet werden (%s)!" % error
#
#            def error(text):
#                gui.main_window.change_status(-1, text)
#        
#            GeneratorTask(download_torrent, error).start(url, dialog.filename)

            download = Download(app.config, dialog.filename)
            download.download_torrent() 

        else: # normal
            
            if options[1] == 'decode':            
                download = Download(app.config, dialog.filename, link=options[2])
                download.download_decode()
                                                    
            elif options[1] == 'decodeandcut':                
                download = Download(app.config, dialog.filename, link=options[2])
                download.download_decode(options[3])   
                             
            else:          
                download = Download(app.config, dialog.filename, link=options[1])
                download.download_basic(app.config.get('downloader', 'preferred_downloader'))
                
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
