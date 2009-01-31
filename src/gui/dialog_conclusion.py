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

from os.path import basename

import gtk

from basewindow import BaseWindow
from constants import Action, Status, Cut_action

class DialogConclusion(BaseWindow):
    
    def __init__(self, app, parent):
        self.app = app
    
        widgets = [
            'buttonBack',
            'buttonForward',
            'buttonClose',
            'labelCount',
            'tableConclusion',
            'labelConclusionFilename',
            'labelConclusionCutStatus',
            'labelConclusionDecodeStatus',
            'labelConclusionCut',
            'labelConclusionDecode',
            'checkbuttonRate',
            'vboxRating',
            'vboxButtons',
            'radiobuttonRate0',
            'radiobuttonRate1',
            'radiobuttonRate2',
            'radiobuttonRate3',
            'radiobuttonRate4',
            'radiobuttonRate5'
            ]
        
        builder = self.create_builder("dialog_conclusion.ui")
            
        BaseWindow.__init__(self, builder, "dialog_conclusion", widgets, parent)
                
        # setup widgets
        for radio in range(6):
            self.get_widget("radiobuttonRate" + str(radio)).connect('toggled', self.on_radiobuttonRating_toggled, radio)
    
    ###
    ### Convenience
    ###        
    
    def build(self, file_conclusions, action):
        dialog = self.get_window()
        dialog.show_all()
        
        for radio in ['radiobuttonRate0', 'radiobuttonRate1', 'radiobuttonRate2', 'radiobuttonRate3', 'radiobuttonRate4', 'radiobuttonRate5' ]:
            self.get_widget(radio).set_sensitive(False)
        
        self.action = action

        # show status/rating for decode/cut?
        if self.action==Action.DECODE:
            self.get_widget('labelConclusionCutStatus').hide()
            self.get_widget('labelConclusionCut').hide()   
            self.get_widget('vboxRating').hide()
        elif self.action==Action.CUT:
            self.get_widget('labelConclusionDecodeStatus').hide()
            self.get_widget('labelConclusionDecode').hide()   
                        
        self.file_conclusions = file_conclusions
                
        self.show_conclusion(0)       
        return dialog        
     
    ###
    ### Helpers
    ###
     
    def __status_to_s(self, status):
        if status==Status.OK:
            return "OK"
        elif status==Status.ERROR:
            return "Fehler"
        elif status==Status.NOT_DONE:
            return "Nicht durchgeführt"
     
    ###
    ### Signals handlers
    ###
        
    def on_buttonConclusionPlay_clicked(self, widget, data=None):    
        if self.action==Action.DECODE or self.file_conclusions[self.conclusion_iter].cut.status != Status.OK:
            filename = self.file_conclusions[self.conclusion_iter].uncut_avi
        else:    
            filename = self.file_conclusions[self.conclusion_iter].cut_avi

        self.app.perform_action(Action.PLAY, [filename])      
        
    def on_radiobuttonRating_toggled(self, widget, rate):
        if widget.get_active()==True:            
            self.file_conclusions[self.conclusion_iter].cut.rating = rate 
       
    def on_checkbuttonRate_toggled(self, widget, data=None):
        status = widget.get_active()

        if status==False:
            self.get_widget('radiobuttonRate0').set_active(True)
            self.file_conclusions[self.conclusion_iter].cut.rating = -1
        
        for radio in ['radiobuttonRate0', 'radiobuttonRate1', 'radiobuttonRate2', 'radiobuttonRate3', 'radiobuttonRate4', 'radiobuttonRate5' ]:
            self.get_widget(radio).set_sensitive(status)
        
    def on_buttonBack_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter - 1)
    
    def on_buttonForward_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter + 1)
        
    def show_conclusion(self, new_iter):
        self.conclusion_iter = new_iter
        
        # reset dialog        
        self.get_widget('labelCount').set_text("Zeige Datei %s/%s" % (self.conclusion_iter + 1, len(self.file_conclusions)))
        self.get_widget('vboxRating').hide()
        self.get_widget('vboxButtons').hide()
        
        # enable back-button?
        if self.conclusion_iter==0:
            self.get_widget('buttonBack').set_sensitive(False)
        else:
            self.get_widget('buttonBack').set_sensitive(True)
        
        # enable forward-button?
        if self.conclusion_iter + 1 == len(self.file_conclusions):
            self.get_widget('buttonForward').set_sensitive(False)
        else:
            self.get_widget('buttonForward').set_sensitive(True)
                
        # conclusion of file
        file_conclusion = self.file_conclusions[self.conclusion_iter]
        
        # filename
        if self.action == Action.CUT:
            filename = file_conclusion.uncut_avi
        else:
            # remove ugly .otrkey
            filename = file_conclusion.otrkey[0:len(file_conclusion.otrkey)-7]
                          
        self.get_widget('labelConclusionFilename').set_text(basename(filename))  
        
        # decode status
        if self.action != Action.CUT:
            text = self.__status_to_s(file_conclusion.decode.status)
            message = file_conclusion.decode.message
            if message != "":
                text += " (%s)" % message
            
            if file_conclusion.decode.status==Status.OK:
                self.get_widget('vboxButtons').show()
                            
            self.get_widget('labelConclusionDecodeStatus').set_text(text)
        
        # cut status
        if self.action != Action.DECODE:
            text = self.__status_to_s(file_conclusion.cut.status)
            message = file_conclusion.cut.message
            
            if message != "":
                text += " (%s)" % message
           
            if file_conclusion.cut.cut_action != -1 and file_conclusion.cut.status==Status.OK:
                if file_conclusion.cut.cut_action == Cut_action.MANUALLY:
                    text += ", Manuell geschnitten"
                else:
                    text += ", Geschnitten mit Cutlist #%s" % file_conclusion.cut.cutlist
                    # enable rating options and play option
                    self.get_widget('vboxRating').show()
                    self.get_widget('vboxButtons').show()
                    
                    # already rated?
                    if file_conclusion.cut.rating > -1:                               
                        self.get_widget('checkbuttonRate').set_active(True)
                        self.get_widget('radiobuttonRate' + str(file_conclusion.cut.rating)).set_active(True)
                    else:
                        self.get_widget('checkbuttonRate').set_active(False)
                                       
            self.get_widget('labelConclusionCutStatus').set_text(text) 


    def on_buttonConclusionClose_clicked(self, widget, data=None):
        self.hide()
