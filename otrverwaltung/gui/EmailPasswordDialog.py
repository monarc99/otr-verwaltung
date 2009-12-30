#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from otrverwaltung import path

class EmailPasswordDialog(gtk.Dialog, gtk.Buildable):
    __gtype_name__ = "EmailPasswordDialog"

    def __init__(self):
        pass

    def do_parser_finished(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)
        self.builder.get_object('entryDialogPassword').set_visibility(False)
    
    def set_email_password(self, email, password):
        self.builder.get_object('entryDialogEMail').set_text(email)
        self.builder.get_object('entryDialogPassword').set_text(password)
    
    def get_email_password(self):
        return self.builder.get_object('entryDialogEMail').get_text(), self.builder.get_object('entryDialogPassword').get_text()
        
def NewEmailPasswordDialog():
    glade_filename = path.getdatapath('ui', 'EmailPasswordDialog.glade')
    
    builder = gtk.Builder()   
    builder.add_from_file(glade_filename)
    dialog = builder.get_object("email_password_dialog")
        
    return dialog
