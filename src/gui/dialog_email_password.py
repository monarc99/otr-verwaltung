#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

from basewindow import BaseWindow

class DialogEmailPassword(BaseWindow):
    
    def __init__(self, parent):             
        BaseWindow.__init__(self, "dialog_email_password.ui", "dialog_email_password", parent)
        
        self.get_widget('entryDialogPassword').set_visibility(False)
