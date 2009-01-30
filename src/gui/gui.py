#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OTR-Verwaltung 0.9 (Beta 1)
# Copyright (C) 2008 Benjamin Elbers (elbersb@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

try:
    import gtk
    import pygtk
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)


from main_window import MainWindow
from preferences_window import PreferencesWindow
from dialog_archive import DialogArchive
from dialog_conclusion import DialogConclusion
from dialog_cut import DialogCut
from dialog_cutlist import DialogCutlist
from dialog_email_password import DialogEmailPassword
from dialog_rename import DialogRename
from dialog_planning import DialogPlanning

class Gui:
    def __init__(self, app):
        self.app = app
    
        # TODO: icons setzen, aber wo?
        # for window in self.windows:
        #   self.windows[window].set_icon(gtk.gdk.pixbuf_new_from_file(self.get_image_path('icon3.png')))      
        
        # TODO: einheitliches benennungsschema für widgets: MainWindow oder main_window
        # TODO: signal-methoden mit präfix __: def on_button_clicked -> def __on_button_clicked?
        self.main_window = MainWindow(app, self)
        self.preferences_window = PreferencesWindow(app, self, self.main_window)
        self.dialog_archive = DialogArchive(self.main_window)
        self.dialog_conclusion = DialogConclusion(app, self.main_window)
        self.dialog_cut = DialogCut(self.main_window)
        self.dialog_cutlist = DialogCutlist(self.main_window)
        self.dialog_email_password = DialogEmailPassword(self.main_window)
        self.dialog_rename = DialogRename(self.main_window)
        self.dialog_planning = DialogPlanning(self, self.main_window)

    def run(self):
        gtk.main()

    # 
    # Dialogs
    #

    def message_info_box(self, message_text):
        dialog = self.__get_dialog(gtk.MESSAGE_INFO, gtk.BUTTONS_OK, \
                                                                message_text)
                
        result = dialog.run()
        dialog.destroy()
        
    def message_error_box(self, message_text):
        dialog = self.__get_dialog(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, \
                                                                message_text)
                    
        dialog.run()
        dialog.destroy()
    
    def question_box(self, message_text):
        dialog = self.__get_dialog(gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, \
                                                                message_text)
               
        result = dialog.run()
        dialog.destroy()
        
        return result==gtk.RESPONSE_YES
        
    def __get_dialog(self, message_type, message_buttons, message_text):
        return gtk.MessageDialog(
                    self.main_window.get_window(),
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    message_type,
                    message_buttons,
                    message_text)
                    

if __name__ == "__main__":
    print "Usage: otr.py"
    sys.exit(-1)
