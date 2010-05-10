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
import os.path
from otrverwaltung.gui import AddDownloadDialog
from otrverwaltung.downloader import Download
from otrverwaltung import fileoperations
from otrverwaltung.constants import DownloadStatus

from otrverwaltung.actions.baseaction import BaseAction

def add_download(via_link, app, gui, link=None):
    if link:
        link = link.replace("otr://", "")

    dialog = AddDownloadDialog.NewAddDownloadDialog(gui, app.config, via_link, link)
        
    if dialog.run() == gtk.RESPONSE_OK:           
        options = dialog.get_download_options()
                
        if options[0] == 'torrent':
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

class Remove(BaseAction):
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self, downloads):
        downloads_count = len(downloads)
        if downloads_count == 1:
            question = "Soll der Download wirklich entfernt werden?"
        else:
            question = "Sollen %i Downloads wirklich entfernt werden?" % downloads_count

        dialog = gtk.MessageDialog(self.__gui.main_window, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, question)
        checkbutton = gtk.CheckButton('Die heruntergeladene Datei in den Müll verschieben\n(Fertige Downloads werden nicht verschoben)')
        checkbutton.set_active(True)
        checkbutton.show()
        dialog.vbox.pack_end(checkbutton)
        response = dialog.run()

        if response == gtk.RESPONSE_YES:
            model = self.__gui.main_window.treeview_download.get_model()

            refs = []
            for row in model:
                if row[0] in downloads:
                    refs.append(gtk.TreeRowReference(model, row.path))

                    files = [
                        os.path.join(row[0].information['output'], row[0].filename + '.torrent'),
                        os.path.join(row[0].information['output'], row[0].filename + '.aria2'),
                        os.path.join(row[0].information['output'], row[0].filename + '.cutlist'),
                        os.path.join(self.__app.config.get('general', 'folder_trash_otrkeys'), row[0].filename + '.segments'),
                    ]

                    for file in files:
                        if os.path.exists(file):
                            fileoperations.remove_file(file, None)

                    if checkbutton.get_active() and not row[0].information['status'] in [DownloadStatus.FINISHED, DownloadStatus.SEEDING]:
                        otrkey = os.path.join(row[0].information['output'], row[0].filename)
                        # move otrkey to trash
                        if os.path.exists(otrkey):
                            fileoperations.move_file(otrkey, self.__app.config.get('general', 'folder_trash_otrkeys'), None)
                        # move avi file of otrdecoder to trash
                        avi_file = os.path.splitext(otrkey)[0]
                        if os.path.exists(avi_file):
                            fileoperations.move_file(avi_file, self.__app.config.get('general', 'folder_trash_avis'), None)

                    row[0].stop()

            for ref in refs:
                iter = model.get_iter(ref.get_path())
                model.remove(iter)

        dialog.destroy()
