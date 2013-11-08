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

""" Stellt Methoden für Dateioperationen bereit. 
Zeigt bei Fehlern einen gtk.MessageDialog an."""

import gtk
import os
import shutil
from os.path import join, basename, exists, dirname, splitext

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

def handle_error(error_cb, message):
    if error_cb:
        error_cb(message)
    else:
        print message
                    
def remove_file(filename, error_cb=__error):
    """ Entfernt die angegebene Datei. """

    print "[Fileoperations] Remove ", filename
    try:
        os.remove(filename)
    except Exception, e:
        handle_error(error_cb, "Fehler beim Löschen von %s (%s)." % (filename, e))
    
def rename_file(old_filename, new_filename, error_cb=__error):
    """ Benennt eine Datei um. Wenn die Datei bereits existiert, wird der neue Name um eine Zahl erweitert. """
       
    if old_filename == new_filename:
        handle_error(error_cb, "Umbenennen: Die beiden Dateinamen stimmen überein! (%s)" % old_filename)
        return

    new_filename = make_unique_filename(new_filename)
    
    print "[Fileoperations] Rename %s to %s" % (old_filename, new_filename)
        
    try:        
        os.rename(old_filename, new_filename)
    except Exception, e:
        handle_error(error_cb, "Fehler beim Umbenennen von %s nach %s (%s)." % (old_filename, new_filename, e))
        return
    
    return new_filename

def move_file(filename, target, error_cb=__error):
    """ Verschiebt eine Datei in den angegebenen Ordner."""
    """ return: new filename """
    
    new_filename = join(target, basename(filename))
    
    if exists(new_filename):
        handle_error(error_cb, "Umbenennen: Die Datei existiert bereits! (%s)" % new_filename)
        return filename
    
    print "[Fileoperations] Move %s to %s" % (filename, target)
    try:
        os.rename(filename, new_filename)
    except OSError, e:
        try:
            shutil.move(filename, target)
        except Exception:
            handle_error(error_cb, "Fehler beim Verschieben von %s nach %s (%s). " % (filename, target, e))
            return filename
            
    if os.path.isfile(filename +'.cutlist'):
        os.remove(filename +'.cutlist')
    return new_filename

def make_unique_filename(filename):
    """ Gleicht den gegebenen Dateinamen an, sodass  """
    new_filename = filename
    count = 1
    while exists(new_filename):
        path, extension = splitext(filename)
        new_filename = "%s.%i%s" % (path, count, extension)
        count += 1

    return new_filename

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
