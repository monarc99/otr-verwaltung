#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import gtk
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

from main_window import MainWindow
from preferences_window import PreferencesWindow
from dialog_archive import DialogArchive
from dialog_conclusion import DialogConclusion
from dialog_cut import DialogCut
from dialog_email_password import DialogEmailPassword
from dialog_rename import DialogRename
from dialog_planning import DialogPlanning
from dialog_plugins import DialogPlugins

import otrpath

class Gui:
    def __init__(self, app):
        self.app = app
           
        # TODO: einheitliches benennungsschema für widgets: MainWindow oder main_window        
        self.main_window = MainWindow(app, self)
        self.preferences_window = PreferencesWindow(app, self, self.main_window)
        self.dialog_archive = DialogArchive(self.main_window)
        self.dialog_conclusion = DialogConclusion(app, self, self.main_window)
        self.dialog_cut = DialogCut(app, self, self.main_window)
        self.dialog_email_password = DialogEmailPassword(self.main_window)
        self.dialog_rename = DialogRename(self.main_window)
        self.dialog_planning = DialogPlanning(self, self.main_window)
        self.dialog_plugins = DialogPlugins(self, self.main_window)

        for window in [self.main_window]:
            window.get_window().set_icon(gtk.gdk.pixbuf_new_from_file(otrpath.get_image_path('icon3.png')))      

    def run(self):
        gtk.main()

    #
    # Helpers
    #
    
    def set_model_from_list(self, cb, items):
        """Setup a ComboBox or ComboBoxEntry based on a list of strings."""           
        model = gtk.ListStore(str)
        for i in items:
            model.append([i])
        cb.set_model(model)
        if type(cb) == gtk.ComboBoxEntry:
            cb.set_text_column(0)
        elif type(cb) == gtk.ComboBox:
            cell = gtk.CellRendererText()
            cb.pack_start(cell, True)
            cb.add_attribute(cell, 'text', 0)            

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
