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
import base64
import urllib
import hashlib

from otrverwaltung.actions.baseaction import BaseAction

class Add(BaseAction):
    def __init__(self, app, gui):
        self.update_list = False
        self.__app = app
        self.__gui = gui

    def do(self):
        dialog = AddDownloadDialog.NewAddDownloadDialog(self.__gui, self.__app.config)
        
        if dialog.run() == gtk.RESPONSE_OK:           
            options = dialog.get_download_options()
            
            password = base64.b64decode(self.__app.config.get('general', 'password')) 
            
            if options[0] == 'torrent':
                user_id = options[1]
                hash = hashlib.md5(password).hexdigest()
                
                url = 'http://81.95.11.2/xbt/xbt_torrent_create.php?filename=%s&userid=%s&mode=free&hash=%s' % (dialog.filename, user_id, hash)
                # TODO: Error handling
                urllib.urlretrieve(url, "/tmp/torrent")
                
                command = ['xdg-open', '/tmp/torrent' ]
            
            else: # normal
                email = self.__app.config.get('general', 'email')                
                cache_dir = self.__app.config.get('general', 'folder_trash_otrkeys')
                decoder = self.__app.config.get('general', 'decoder')
                
                if options[1] == 'decode':
                    output = self.__app.config.get('general', 'folder_uncut_avis')
                    
                    command = [decoder, "-n", "-i", options[2], "-o", output, "-c", cache_dir, "-e", email, "-p", password]
                    
                elif options[1] == 'decodeandcut':
                    server = self.__app.config.get('general', 'server')
                    output = self.__app.config.get('general', 'folder_cut_avis')
                    cutlist_link = "%sgetfile.php?id=%s" % (server , options[3])
                                    
                    command = [decoder, "-n", "-i", options[2], "-o", output, "-c", cache_dir, "-e", email, "-p", password, "-C", cutlist_link]
                else:                
                    output = self.__app.config.get('general', 'folder_new_otrkeys')
                    command = ["wget", "-c", "-P", output, options[1]]
            
            print
            print " ".join(command)
            print
            
            dialog.destroy()
        else:
            dialog.destroy()
            return
            
                

