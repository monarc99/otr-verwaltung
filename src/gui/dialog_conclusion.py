#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, pango
import os.path

from basewindow import BaseWindow

from constants import Action, Status, Cut_action

class DialogConclusion(BaseWindow):
    """ The dialog is organized in boxes:
            box_filenames - Shows the filename and the statuses of a decode/cut action.
            box_buttons - Play button, Cut-Play button, Put uncut file in trash, box_rename, box_rating
            box_create_cutlist - Settings for a cutlist. 
                

        If cut.status == status.OK:                 v=Visible, x!=not visible
        
                          BEST_CUTLIST  CHOOSE_CUTLIST  LOCAL_CUTLIST  MANUALLY
        button_play           V               V              V            V
        button_play_cut       V               V              V            V
        combobox_external_r   V               V              x!           x!       !
        check_delete_uncut    V               V              V            V
        box_rename            V               V              V            V 
        box_create_cutlist    x!              x!             x!           V        !     
                    
                """
        
    def __init__(self, app, gui, parent):
        self.app = app
        self.gui = gui
           
        BaseWindow.__init__(self, "dialog_conclusion", parent)       
                
        self.get_widget('check_create_cutlist').modify_font(pango.FontDescription("bold"))
              
        for combobox in ['combobox_external_rating', 'combobox_own_rating']:
            cell = gtk.CellRendererText()
            cell.set_property('ellipsize', pango.ELLIPSIZE_END)
            self.get_widget(combobox).pack_start(cell, True)
            self.get_widget(combobox).add_attribute(cell, 'text', 0)
        
    ###
    ### Convenience
    ###        
    
    def run(self, file_conclusions, action, rename_by_schema):
        self.action = action
        self.rename_by_schema = rename_by_schema                       
        self.__file_conclusions = file_conclusions
        self.forward_clicks = 0

        self.get_window().show_all()
                
        # basic show/hide
        widgets_hidden = []
        if self.action == Action.DECODE:
            self.get_widget('box_buttons').show() # show buttons, but hide all except play button
            widgets_hidden = ['image_cut', 'label_cut', 'label_cut_status', 'button_play_cut', 'box_rating', 'check_delete_uncut', 'box_rename']            
        elif self.action == Action.CUT:
            widgets_hidden = ['image_decode', 'label_decode', 'label_decode_status']
            
        for widget in widgets_hidden:
            self.get_widget(widget).hide()
                
        self.show_conclusion(0)       

        self.get_window().run()
        self.hide()
        return self.__file_conclusions
        
    def __status_to_s(self, status, message):
        string = ''
            
        if status == Status.OK:
            string = "OK"
        elif status == Status.ERROR:
            string = "Fehler"
        elif status == Status.NOT_DONE:
            string = "Nicht durchgeführt"
            
        if message:
            if "No connection to server" in message:
                message = "Keine Verbindung zum Server"
            elif "Output file already exists" in message:
                message = "Ausgabedatei existiert bereits"
            
            if status == Status.ERROR:
                message = "<b>%s</b>" % message
            
            string += ": %s" % unicode(message, "iso-8859-15")
                
        return string                
                
    ###
    ### Controls
    ###

    def _on_button_back_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter - 1)
    
    def _on_button_forward_clicked(self, widget, data=None):
        self.show_conclusion(self.conclusion_iter + 1)
        self.forward_clicks += 1
        
    def show_conclusion(self, new_iter):
        self.conclusion_iter = new_iter
        self.file_conclusion = self.__file_conclusions[self.conclusion_iter]
        self.get_widget('label_count').set_text("Zeige Datei %s/%s" % (str(new_iter + 1), len(self.__file_conclusions)))

        # enable back- and forward button?
        self.get_widget('button_back').set_sensitive(not self.conclusion_iter == 0)
        self.get_widget('button_forward').set_sensitive(not (self.conclusion_iter + 1 == len(self.__file_conclusions)))               
                
        # status message
        if self.action != Action.DECODE:
            status, message = self.file_conclusion.cut.status, self.file_conclusion.cut.message
            self.get_widget('label_cut_status').set_markup(self.__status_to_s(status, message))
            self.get_widget('label_filename').set_markup("<b>%s</b>" % os.path.basename(self.file_conclusion.uncut_video))
        
        if self.action != Action.CUT:
            status, message = self.file_conclusion.decode.status, self.file_conclusion.decode.message
            self.get_widget('label_decode_status').set_markup(self.__status_to_s(status, message))
            self.get_widget('label_filename').set_markup("<b>%s</b>" % os.path.basename(self.file_conclusion.otrkey))
        
        # fine tuning              
        if self.action == Action.DECODE:
            self.get_widget('box_create_cutlist').hide()
        
        else:
            cut_ok = (self.file_conclusion.cut.status == Status.OK)
            cut_action = self.file_conclusion.cut.cut_action
                        
            # set visibility
            self.get_widget('button_play').props.visible = cut_ok
            self.get_widget('button_play_cut').props.visible = cut_ok           
            
            self.get_widget('check_delete_uncut').props.visible = cut_ok            
            if cut_ok:
                self.get_widget('check_delete_uncut').set_active(self.file_conclusion.cut.delete_uncut)
            
            self.get_widget('box_rename').props.visible = cut_ok           
            
            if cut_ok:        
                rename_list = [os.path.basename(self.file_conclusion.cut_video), self.rename_by_schema(os.path.basename(self.file_conclusion.uncut_video))]
                
                if self.file_conclusion.cut.cutlist.filename:
                    rename_list.append(self.file_conclusion.cut.cutlist.filename)
                    
                    self.get_widget('comboboxentry_rename').child.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color("#FFFF84"))
                else:
                    self.get_widget('comboboxentry_rename').child.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color("white"))
                
                self.gui.set_model_from_list(self.get_widget('comboboxentry_rename'), rename_list)     
                self.get_widget('comboboxentry_rename').child.set_text(self.file_conclusion.cut.rename)

            if cut_action == Cut_action.BEST_CUTLIST or cut_action == Cut_action.CHOOSE_CUTLIST:
                self.get_widget('box_rating').props.visible = cut_ok
                self.get_widget('combobox_external_rating').set_active(self.file_conclusion.cut.my_rating + 1)
                
                if cut_ok:
                    text = self.get_widget('label_cut_status').get_text()
                    
                    text += "\nMit Cutlist %s geschnitten: Autor: <b>%s</b>, Wertung: <b>%s</b>\nKommentar: <b>%s</b>" % (self.file_conclusion.cut.cutlist.id, self.file_conclusion.cut.cutlist.author, self.file_conclusion.cut.cutlist.rating, self.file_conclusion.cut.cutlist.usercomment)
                    
                    self.get_widget('label_cut_status').set_markup(text)
            else:
                self.get_widget('box_rating').hide()
                
            if cut_action == Cut_action.MANUALLY:
                self.get_widget('box_create_cutlist').props.visible = cut_ok

                if cut_ok:
                    self.get_widget('check_create_cutlist').set_active(self.file_conclusion.cut.create_cutlist)
                    
                    c = self.file_conclusion.cut.cutlist                    
                    self.get_widget('combobox_own_rating').set_active(c.ratingbyauthor + 1)
                    self.get_widget('check_wrong_content').set_active(c.wrong_content)
                    self.get_widget('entry_actual_content').set_text(c.actualcontent)
                    self.get_widget('check_missing_beginning').set_active(c.missing_beginning)
                    self.get_widget('check_missing_ending').set_active(c.missing_ending)
                    self.get_widget('check_other_error').set_active(c.other_error)
                    self.get_widget('entry_other_error_description').set_text(c.othererrordescription)
                    self.get_widget('entry_suggested').set_text(c.suggested_filename)
                    self.get_widget('entry_comment').set_text(c.usercomment)
            else:
                self.get_widget('box_create_cutlist').hide()
                
        if self.action != Action.CUT:
            self.get_widget('button_play').props.visible = (self.file_conclusion.decode.status == Status.OK)

    ###
    ### Signals handlers
    ###
    
    # box_buttons
    
    def _on_button_play_clicked(self, widget, data=None):
        if self.action == Action.DECODE or (self.action == Action.DECODEANDCUT and self.file_conclusion.cut.status != Status.OK):
            self.app.play_file(self.file_conclusion.uncut_video)
        else:
            self.app.play_file(self.file_conclusion.cut_video)
  
    def _on_button_conclusion_play_cut_clicked(self, widget, data=None):
        self.app.show_cuts_after_cut(self.file_conclusion.cut_video, self.file_conclusion.cut.cutlist)    

    def _on_combobox_external_rating_changed(self, widget, data=None):
        rating = widget.get_active() - 1 
        print "[Conclusion] cut.my_rating = ", rating
        self.file_conclusion.cut.my_rating = rating

    def _on_check_delete_uncut_toggled(self, widget, data=None):
        print "[Conclusion] cut.delete_uncut = ", widget.get_active()
        self.file_conclusion.cut.delete_uncut = widget.get_active()
   
    def _on_comboboxentry_rename_changed(self, widget, data=None):
        print "[Conclusion] cut.rename = ", widget.child.get_text()
        self.file_conclusion.cut.rename = widget.child.get_text()
    
    # box_create_cutlist           
    def _on_check_create_cutlist_toggled(self, widget, data=None):
        create_cutlist = widget.get_active()
        print "[Conclusion] cut.create_cutlist = ", create_cutlist
        self.file_conclusion.cut.create_cutlist = create_cutlist
        self.get_widget('box_create_cutlist_options').set_sensitive(create_cutlist)
        
    def _on_combobox_own_rating_changed(self, widget, data=None):
        ratingbyauthor = widget.get_active() - 1 
        print "[Conclusion] cut.cutlist.ratingbyauthor = ", ratingbyauthor
        self.file_conclusion.cut.cutlist.ratingbyauthor = ratingbyauthor
        
    def _on_check_wrong_content_toggled(self, widget, data=None):
        print "[Conclusion] cut.cutlist.wrong_content = ", widget.get_active()
        self.file_conclusion.cut.cutlist.wrong_content = widget.get_active()

    def _on_entry_actual_content_changed(self, widget, data=None):
        print "[Conclusion] cut.cutlist.actualcontent = ", widget.get_text()
        self.file_conclusion.cut.cutlist.actualcontent = widget.get_text()

    def _on_check_missing_beginning_toggled(self, widget, data=None):
        print "[Conclusion] cut.cutlist.missing_beginning = ", widget.get_active()
        self.file_conclusion.cut.cutlist.missing_beginning = widget.get_active()

    def _on_check_missing_ending_toggled(self, widget, data=None):
        print "[Conclusion] cut.cutlist.missing_ending = ", widget.get_active()        
        self.file_conclusion.cut.cutlist.missing_ending = widget.get_active()

    def _on_check_other_error_toggled(self, widget, data=None):
        print "[Conclusion] cut.cutlist.other_error = ", widget.get_active()
        self.file_conclusion.cut.cutlist.other_error = widget.get_active()

    def _on_entry_other_error_description_changed(self, widget, data=None):
        print "[Conclusion] cut.cutlist.othererrordescription = ", widget.get_text()
        self.file_conclusion.cut.cutlist.othererrordescription = widget.get_text()

    def _on_entry_suggested_changed(self, widget, data=None):
        print "[Conclusion] cut.cutlist.suggested_filename = ", widget.get_text()
        self.file_conclusion.cut.cutlist.suggested_filename = widget.get_text()

    def _on_entry_comment_changed(self, widget, data=None):
        print "[Conclusion] cut.cutlist.usercomment = ", widget.get_text()
        self.file_conclusion.cut.cutlist.usercomment = widget.get_text()
                    
