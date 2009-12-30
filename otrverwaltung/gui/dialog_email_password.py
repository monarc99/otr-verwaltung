#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from otrverwaltung.gui.basewindow import BaseWindow

class DialogEmailPassword(BaseWindow):
    
    def __init__(self, parent):             
        BaseWindow.__init__(self, "dialog_email_password", parent)
        
        self.get_widget('entryDialogPassword').set_visibility(False)
    
    def set_email_password(self, email, password):
        self.get_widget('entryDialogEMail').set_text(email)
        self.get_widget('entryDialogPassword').set_text(password)
    
    def get_email_password(self):
        return self.get_widget('entryDialogEMail').get_text(), self.get_widget('entryDialogPassword').get_text()
