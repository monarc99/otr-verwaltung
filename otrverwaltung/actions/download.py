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
            
            if options[0] == 'torrent':
                print "xdg-open torrent-location"
            else: # normal
                email = self.__app.config.get('general', 'email')
                password = base64.b64decode(self.__app.config.get('general', 'password')) 
                
                if options[1] == 'decode':
                    print "exec: ./otrdecoder -n -i %s -o %s -e %s -p %s" % (options[2], self.__app.config.get('general', 'folder_uncut_avis'), email, password)
                elif options[1] == 'decodeandcut':
                    print "download (link: %s) and decode and cut with cutlist #%s by qotr" % (options[2], options[3])
                    print "exec: ./otrdecoder -n -i %s -o %s -e %s -p %s -C %sgetfile.php?id=%s" % (options[2], self.__app.config.get('general', 'folder_cut_avis'), email, password, self.__app.config.get('general', 'server') , options[3])
                else:                
                    print "exec: wget %s" % options[1]
            
            dialog.destroy()
        else:
            dialog.destroy()
            return
            
                

