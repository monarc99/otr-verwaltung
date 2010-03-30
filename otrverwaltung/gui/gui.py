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

try:
    import gtk
except:
    print "PyGTK/GTK is missing."
    sys.exit(-1)

from otrverwaltung.gui import MainWindow, PreferencesWindow, ArchiveDialog, ConclusionDialog, CutDialog, EmailPasswordDialog, RenameDialog, PlanningDialog, PluginsDialog

from otrverwaltung import path

class Gui:
    
    def __init__(self, app):
        self.app = app
           
        # TODO: einheitliches benennungsschema für widgets: MainWindow oder main_window        
        self.main_window = MainWindow.NewMainWindow(app, self)        
        self.main_window.post_init()
        self.preferences_window = PreferencesWindow.NewPreferencesWindow(app, self)
        self.preferences_window.bind_config(app.config)
        
        self.dialog_archive = ArchiveDialog.NewArchiveDialog()
        self.dialog_conclusion = ConclusionDialog.NewConclusionDialog(app, self)
        self.dialog_cut = CutDialog.NewCutDialog(app, self)
        self.dialog_email_password = EmailPasswordDialog.NewEmailPasswordDialog()
        self.dialog_rename = RenameDialog.NewRenameDialog()
        self.dialog_planning = PlanningDialog.NewPlanningDialog(self)
        self.dialog_plugins = PluginsDialog.NewPluginsDialog(self)

        for window in [self.main_window]:
            window.set_icon(gtk.gdk.pixbuf_new_from_file(path.get_image_path('icon3.png')))      

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
        
        return result == gtk.RESPONSE_YES
        
    def __get_dialog(self, message_type, message_buttons, message_text):
        return gtk.MessageDialog(
                    self.main_window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    message_type,
                    message_buttons,
                    message_text)
                    

if __name__ == "__main__":
    print "Usage: otr.py"
    sys.exit(-1)
