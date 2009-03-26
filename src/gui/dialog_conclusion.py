#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import basename, exists

import gtk

from basewindow import BaseWindow
from constants import Action, Status, Cut_action

class DialogConclusion(BaseWindow):
    
    def __init__(self, app, parent):
        self.app = app
            
        BaseWindow.__init__(self, "dialog_conclusion.ui", "dialog_conclusion", parent)
                
        # setup widgets

        # cutlist rating
        for radio in range(6):
            name = "radiobuttonRate" + str(radio)
            self.get_widget(name).connect('toggled', self.on_radiobuttonRating_toggled, radio)
            self.get_widget(name).set_sensitive(False)    
        
        # cutlist create rating
        for radio in range(6):
            name = "radio_create_rate_" + str(radio)
            self.get_widget(name).connect('toggled', self.on_radio_create_rate_toggled, radio)
        
        # rename buttons
        self.rename_radio_buttons = ['radio_no_rename', 'radio_otr_rename', 'radio_filename_rename', 'radio_filename_original_rename', 'radio_autoname_rename' ]

        for radio in range(5):            
            self.get_widget(self.rename_radio_buttons[radio]).connect('toggled', self.on_radio_rename_toggled, radio)

    ###
    ### Convenience
    ###        
    
    def build(self, file_conclusions, action, rename_by_schema, use_rename_by_schema):
        dialog = self.get_window()
        dialog.show_all()
                   
        self.action = action
        self.rename_by_schema = rename_by_schema
        self.use_rename_by_schema = use_rename_by_schema

        # show status/rating for decode/cut?
        if self.action == Action.DECODE:
            self.get_widget('labelConclusionCutStatus').hide()
            self.get_widget('labelConclusionCut').hide()   
            self.get_widget('vboxRating').hide()
            self.get_widget('table_rename').hide()
            self.get_widget('check_delete_uncut').hide()
            self.get_widget('button_conclusion_play_cut').hide()
            
        elif self.action == Action.CUT:
            self.get_widget('labelConclusionDecodeStatus').hide()
            self.get_widget('labelConclusionDecode').hide()   
                        
        self.file_conclusions = file_conclusions
                
        self.show_conclusion(0)       
        
        return dialog        
     
    ###
    ### Helpers
    ###
     
    def __status_to_s(self, status):
        if status == Status.OK:
            return "OK"
        elif status == Status.ERROR:
            return "Fehler"
        elif status == Status.NOT_DONE:
            return "Nicht durchgeführt"
     
    ###
    ### Signals handlers
    ###
             
    def on_buttonConclusionPlay_clicked(self, widget, data=None):    
        if self.action == Action.DECODE or self.file_conclusions[self.conclusion_iter].cut.status != Status.OK:
            filename = self.file_conclusions[self.conclusion_iter].uncut_avi
        else:    
            filename = self.file_conclusions[self.conclusion_iter].cut_avi

        self.app.perform_action(Action.PLAY, [filename])      
       
    def on_button_conclusion_play_cut_clicked(self, widget, data=None):
        file_conclusion = self.file_conclusions[self.conclusion_iter]
    
        self.app.show_cuts_after_cut(file_conclusion.cut_avi, file_conclusion.cut.cutlist.cuts)
    
        
    def on_radiobuttonRating_toggled(self, widget, rate):
        if widget.get_active() == True:            
            self.file_conclusions[self.conclusion_iter].cut.my_rating = rate 
    
    def on_check_delete_uncut_toggled(self, widget, data=None):
        print "set to: ", widget.get_active()
        self.file_conclusions[self.conclusion_iter].cut.delete_uncut = widget.get_active()
       
    def on_checkbuttonRate_toggled(self, widget, data=None):
        status = widget.get_active()

        if status == False:
            self.get_widget('radiobuttonRate0').set_active(True)
            self.file_conclusions[self.conclusion_iter].cut.rating = -1
        
        for radio in ['radiobuttonRate0', 'radiobuttonRate1', 'radiobuttonRate2', 'radiobuttonRate3', 'radiobuttonRate4', 'radiobuttonRate5' ]:
            self.get_widget(radio).set_sensitive(status)
    
    def on_radio_rename_toggled(self, widget, radio_count):   
        if widget.get_active():
            self.file_conclusions[self.conclusion_iter].cut.rename = radio_count       
            print self.file_conclusions[self.conclusion_iter].cut.rename
        
    #
    # Create Cutlist
    #

    def on_check_create_cutlist_toggled(self, widget, data=None):       
        self.file_conclusions[self.conclusion_iter].cut.create_cutlist = widget.get_active()

        self.get_widget('hbox_create_cutlist').set_sensitive(widget.get_active())

    def on_radio_create_rate_toggled(self, widget, radio_count):
        if widget.get_active():
            file_conclusion = self.file_conclusions[self.conclusion_iter]
            
            file_conclusion.cut.cutlist.ratingbyauthor = radio_count

    def on_check_wrong_content_toggled(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.wrong_content = widget.get_active()

    def on_entry_actual_content_changed(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.actualcontent = widget.get_text()

    def on_check_missing_beginning_toggled(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.missing_beginning = widget.get_active()

    def on_check_missing_ending_toggled(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.missing_ending = widget.get_active()

    def on_check_other_error_toggled(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.other_error = widget.get_active()

    def on_entry_other_error_description_changed(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.othererrordescription = widget.get_text()

    def on_entry_suggested_changed(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.suggested_filename = widget.get_text()

    def on_entry_comment_changed(self, widget, data=None):
        self.file_conclusions[self.conclusion_iter].cut.cutlist.usercomment = widget.get_text()
    
    #
    # Controls
    #

    def on_buttonBack_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter - 1)
    
    def on_buttonForward_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter + 1)
        
    def show_conclusion(self, new_iter):
        self.conclusion_iter = new_iter
        
        # reset dialog        
        self.get_widget('labelCount').set_text("Zeige Datei %s/%s" % (self.conclusion_iter + 1, len(self.file_conclusions)))
       
        self.get_widget('vboxRating').hide()
        self.get_widget('buttonConclusionPlay').hide()
        self.get_widget('check_delete_uncut').hide()
        self.get_widget('button_conclusion_play_cut').hide()
        self.get_widget('table_rename').hide()
        self.get_widget('vbox_create_cutlist').hide()
        
        # enable back-button?
        if self.conclusion_iter == 0:
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
        if self.action == Action.DECODE:
            filename = basename(file_conclusion.otrkey)
        else:
            filename = "%s\n%s" % (basename(file_conclusion.uncut_avi), basename(file_conclusion.cut_avi))
                          
        self.get_widget('labelConclusionFilename').set_markup("<b>%s</b>" % filename)
        
        # decode status
        if self.action != Action.CUT:
            text = self.__status_to_s(file_conclusion.decode.status)
            message = file_conclusion.decode.message
            if message != "":
                text += " (%s)" % message
            
            if file_conclusion.decode.status == Status.OK:
                self.get_widget('buttonConclusionPlay').show()
                            
            self.get_widget('labelConclusionDecodeStatus').set_text(text)
        
        # cut status
        if self.action != Action.DECODE:
            text = self.__status_to_s(file_conclusion.cut.status)
            message = file_conclusion.cut.message
            
            if message != "":
                text += " (%s)" % message
           
            if file_conclusion.cut.status != Status.OK:
                file_conclusion.cut.delete_uncut = False
            
            else: # OK
                
                self.get_widget('check_delete_uncut').show()
                self.get_widget('check_delete_uncut').set_active(file_conclusion.cut.delete_uncut)
                
                if file_conclusion.cut.cut_action == Cut_action.MANUALLY:
                    text = "Manuell geschnitten"
                    
                    self.get_widget('vbox_create_cutlist').show()
                    
                    if not file_conclusion.cut.cutlist.cuts: # cannot create cutlist!
                        self.get_widget('hbox_create_cutlist').hide()
                        self.get_widget('label_create_cutlist_error').set_text(file_conclusion.cut.create_cutlist_error)
                        self.get_widget('check_create_cutlist').set_sensitive(False)
                        self.get_widget('check_create_cutlist').set_active(False)

                    else:                        
                        # can create cutlist
                        self.get_widget('hbox_create_cutlist').show()
                        self.get_widget('label_create_cutlist_error').set_text("")
                        self.get_widget('check_create_cutlist').set_sensitive(True)
                        self.get_widget('check_create_cutlist').set_active(file_conclusion.cut.create_cutlist)

                        if file_conclusion.cut.create_cutlist:
                            self.get_widget('hbox_create_cutlist').set_sensitive(True)                            
                        
                            c = file_conclusion.cut.cutlist
                        
                            # fill values                            
                            if c.ratingbyauthor:
                                self.get_widget('radio_create_rate_' + str(c.ratingbyauthor)).set_active(True)
                            
                            self.get_widget('check_wrong_content').set_active(c.wrong_content)
                            self.get_widget('entry_actual_content').set_text(c.actualcontent)
                            self.get_widget('check_missing_beginning').set_active(c.missing_beginning)
                            self.get_widget('check_missing_ending').set_active(c.missing_ending)
                            self.get_widget('check_other_error').set_active(c.other_error)
                            self.get_widget('entry_other_error_description').set_text(c.othererrordescription)
                            self.get_widget('entry_suggested').set_text(c.suggested_filename)
                            self.get_widget('entry_comment').set_text(c.usercomment)
                        else:
                            self.get_widget('hbox_create_cutlist').set_sensitive(False)
                                                               
                else:
                    if file_conclusion.cut.cut_action == Cut_action.LOCAL_CUTLIST: 
                        text += ", Mit lokaler Cutlist geschnitten"                       
                    else:
                        text += ", Geschnitten mit Cutlist #%s" % file_conclusion.cut.cutlist.id
                        
                        self.get_widget('vboxRating').show()                
    
                        self.get_widget('table_rename').show()                  
                        
                        # fill values                         
                        rename = file_conclusion.cut.rename

                        if rename != None:       
                            print self.rename_radio_buttons[rename]         
                            self.get_widget(self.rename_radio_buttons[rename]).set_active(True)
                        elif self.use_rename_by_schema:
                            self.get_widget('radio_otr_rename').set_active(True)                          
                            
                        self.__set_rename('otr_rename', self.rename_by_schema(basename(file_conclusion.uncut_avi)))
                        self.__set_rename('filename_rename', file_conclusion.cut.cutlist.filename)
                        self.__set_rename('filename_original_rename', file_conclusion.cut.cutlist.filename_original)
                        self.__set_rename('autoname_rename', file_conclusion.cut.cutlist.autoname)                      
        
                    # enable play options
                    self.get_widget('buttonConclusionPlay').show()
                    self.get_widget('button_conclusion_play_cut').show()
                    
                    # already rated?
                    if file_conclusion.cut.my_rating > -1:                               
                        self.get_widget('checkbuttonRate').set_active(True)
                        self.get_widget('radiobuttonRate' + str(file_conclusion.cut.my_rating)).set_active(True)
                    else:
                        self.get_widget('checkbuttonRate').set_active(False)            
             
            print text                           
            self.get_widget('labelConclusionCutStatus').set_text(text) 

    def __set_rename(self, name, value):
        radio = self.get_widget('radio_' + name)
        label = self.get_widget('label_' + name)
        
        label.set_text(value)

        print value
        if not value:
            radio.set_sensitive(False)
        else:
            radio.set_sensitive(True)
