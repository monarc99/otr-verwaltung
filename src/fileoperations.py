#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Stellt Methoden für Dateioperationen bereit. 
Zeigt bei Fehlern einen gtk.MessageDialog an."""

import os
import shutil
from os.path import join, basename, exists

# TODO: Achten auf :/\* etc. in Dateiname!
# TODO: Fehler abfangen, fehlerwert zurückgeben, damit das Programm weitermachen kann

def __error(message_text):
    dialog = gtk.MessageDialog(
                None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, 
                gtk.BUTTONS_OK,
                message_text)
                
    dialog.run()
    dialog.destroy()
                    
def remove_file(filename):
    """ Entfernt die angegebene Datei. """

    print "[Fileoperations] Remove ", filename
    try:
        os.remove(filename)
    except Exception, e:
        __error("Fehler beim Löschen von %s (%s)." % (filename, e))
    
def rename_file(old_filename, new_filename):
    """ Benennt eine Datei um. Wenn die Datei bereits existiert, wird der neue Name um eine Zahl erweitert. """
    
    print "[Fileoperations] Rename %s to %s" % (old_filename, new_filename)
    
    if old_filename == new_filename:
        __error("Umbenennen: Die beiden Dateinamen stimmen überein! (%s)" % old_filename)
        return

    count = 1
    while exists(new_filename):                  
        new_filename = new_filename.split('.')
        new_filename = "".join(new_filename[0:len(new_filename)-1]) + "." + str(count) + "." + new_filename[len(new_filename)-1]
        count += 1
        
    try:        
        os.rename(old_filename, new_filename)
    except Exception, e:
        __error("Fehler beim Umbenennen von %s nach %s (%s)." % (old_filename, new_filename, e))

def move_file(filename, target):
    """ Verschiebt eine Datei in den angegebenen Ordner. Wenn die Datei im gewählten Ordner 
    bereits existiert, wird der neue Name um eine Zahl erweitert. """
    
    print "[Fileoperations] Move %s to %s" % (filename, target)
    try:
        os.rename(filename, join(target, basename(filename)))
    except OSError, e:
        try:
            shutil.move(filename, target)
        except Exception:
            __error("Fehler beim Verschieben von %s nach %s (%s). " % (filename, target, e))

def get_size(filename):
    """ Gibt die Dateigröße in Bytes zurück. """
    filestat = os.stat(filename)
    size = filestat.st_size
    
    return size

def get_date(filename):
    """ Gibt das Datum, an dem die Datei zuletzt geändert wurde, zurück."""
    filestat = os.stat(filename)
    date = filestat.st_mtime
    
    return date
