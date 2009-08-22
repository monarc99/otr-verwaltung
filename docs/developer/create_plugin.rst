Tutorial: Ein Plugin erstellen
==============================

Eine Anleitung, wie man ein Plugin für OTR-Verwaltung schreibt

Einführung
##########

Mit einem Plugin lassen sich die Funktionen von OTR-Verwaltung erweitern. 
Die Plugins werden in `Python <http://www.python.org/>`_ geschrieben.
Im folgenden wird beschrieben, wie man ein einfaches Plugin selbst programmiert.
Das Plugin soll auf Knopfdruck mit Hilfe einer Mirrorsuchmaschine ähnliche Sendungen finden.

.. highlight:: python
        :linenothreshold: 3

Grundlagen
##########

OTR-Verwaltung lädt Plugins aus zwei Ordnern, wenn es installiert ist: ``~/.otr-verwaltung/plugins`` und ``/usr/share/otr-verwaltung/plugins``. Letzterer ist für Plugins bestimmt, die von OTR-Verwaltung mitgeliefert werden. Wir erstellen also die Datei ``~/.otr-verwaltung/plugins/FindSimilar.py`` mit folgendem Inhalt::
   
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    from pluginsystem import Plugin # 1

    class FindSimilar(Plugin): # 2
        Name = "Ähnliche Sendungen finden" # 3
        Desc = "Sucht bei einer Mirrorsuchmaschine nach ähnlichen Sendungen." # 4
        Author = "Ich"
        Configurable = False # 5
            
        def enable(self): # 6
            pass                  
            
        def disable(self): # 7
            pass   

Erklärungen zu den mit Nummer bezeichneten Kommentaren:

1. Auf diese Weise wird die Basisklasse `~pluginsystem.Plugin` für alle Plugins importiert.
2. **Wichtig:** Der Klassenname und der Dateiname müssen identisch sein. Außerdem muss die Klasse von der Klasse `~pluginsystem.Plugin` abgeleitet sein.
3. Dies sollte ein deutscher Name des Plugins sein.
4. Hier kann eine ausführliche Beschreibung Platz finden.
5. Auf diesen Parameter wird später noch eingegangen. Er bietet die Möglichkeit, dem Plugin Optionen hinzuzufügen.
6. Dieser Code wird ausgeführt, wenn das Plugin aktiviert wird.
7. Dieser Code wird ausgeführt, wenn das Plugin deaktiviert wird.

Wird OTR-Verwaltung nun gestartet, taucht das Plugin *Ähnliche Sendungen finden* in der Liste auf; es kann aktiviert und deaktiviert werden. Allerdings besitzt es noch keine Funktion!

Toolbar
#######

Wenn das Plugin aktiviert wird, muss ein Knopf zur Leiste hinzugefügt werden. Dieser Knopf soll nur in der Ansicht der nicht dekodierten und ungeschnittenen Sendungen angezeigt werden. Dafür bietet OTR-Verwaltung die Funktion `~gui.main_window.MainWindow.add_toolbutton`. Beim Deaktivieren muss der Knopf mit `~gui.main_window.MainWindow.remove_toolbutton` wieder entfernt werden::

    from constants import Section
    import gtk

    ...

    def enable(self):
        self.toolbutton = self.gui.main_window.add_toolbutton(gtk.Image(), 'Ähnliche Sendungen', [Section.OTRKEY, Section.VIDEO_UNCUT]) # 1
        self.toolbutton.connect('clicked', self.find_similar_clicked)  # 2

    def disable(self):
        self.gui.main_window.remove_toolbutton(self.toolbutton)               

    def find_similar_clicked(self, widget, data=None): # 3
        print "Klick!" # 4

Erklärungen zu den mit Nummer bezeichneten Kommentaren:

1. Wir speichern den Toolbutton für die ``disable``-Methode. Außerdem lassen wir das Bild erst einmal leer. 
2. Diese Funktion verbindet das Drücken des Buttons mit der Funktion ``find_similar_clicked``, ...
3. ... die hier definiert ist.
4. Bisher schreiben wir nur "Klick!" ins Terminal, wenn der Knopf gedrückt wird.

Wird OTR-Verwaltung nun gestartet, lässt sich Beobachten, wie beim Aktivieren und Deaktivieren des Plugins der Knopf *Ähnliche Sendungen* auftaucht bzw. verschwindet. Wird der Knopf gedrückt, steht im Terminal "Klick!".

Funktion
########

Die Logik des Plugins befindet sich in der Funktion ``find_similar_clicked``. Diese muss folgendes leisten:

* Den aktuell markierten Dateinamen ermitteln. Sind mehrere Dateien oder keine markiert, soll eine Fehlermeldung angezeigt werden.
* Den Dateinamen so reduzieren, dass ähnliche Sendungen gefunden werden (aus *King_of_Queens_09.05.26_15-30_kabel1_30_TVOON_DE.mpg.avi.otrkey* wird *King_of_Queens*)
* Den Webbrowser starten und die korrekte URL übergeben. ::

    import gtk, re, webbrowser, os.path

    ...

    def find_similar_clicked(self, widget, data=None): 
        filenames = self.gui.main_window.get_selected_filenames() # 1

        if len(filenames) != 1: 
            self.gui.message_error_box("Es muss eine Datei markiert sein.")
            return
            
        filename = os.path.basename(filenames[0]) # 2
        filename_regex = re.compile('(.*)_([0-9]{2}[\.]){2}') # 3
        filename_short = filename_regex.match(filename).groups()[0] # 4
        
        webbrowser.open("http://www.otr-search.com/?q=%s" % filename_short) # 5            

Erklärungen zu den mit Nummer bezeichneten Kommentaren:

1. Auch hier stellt OTR-Verwaltung eine praktische Funktion bereit, die eine Liste von allen markierten Dateinamen zurückgibt (`~gui.main_window.MainWindow.get_selected_filenames`).
2. Die Funktion `os.path.basename <http://docs.python.org/library/os.path.html#os.path.basename>`_ gibt den Namen der Datei ohne Pfadangaben zurück (aus ``/home/ich/eine_datei.avi`` wird ``eine_datei.avi``).
3. Eine kleine Regular Expression, mit der der reduzierte Dateiname ermittelt wird. Sie stimmt überein mit Zeichenketten der Form *irgendwelcher_text_09.05* oder *etwas_anderes_08.13*, darunter fallen also die otrkeys und die ungeschnittenen Video-Dateien.
4. Auf den Inhalt des ersten Klammerpaars der Regular Expression kann mit `groups <http://docs.python.org/library/re.html#re.MatchObject.groups>`_ zugegriffen werden.
5. Schließlich wird der Webbrowser mit der zusammengebauten URL gestartet.

Das Plugin ist nun funktionsfähig. Es soll aber noch eine Option eingebaut werden, mit der die Suchmaschine selbst bestimmt werden kann.

Konfiguration
#############

Das Schöne daran ist, dass OTR-Verwaltung fast alles selbst übernimmt. Man braucht sich keine Gedanken machen, wie man Optionen abspeichert und lädt::


    Configurable = True # 1
    Config = { 'server': 'http://www.otr-search.com/?q=' } # 2

    ...

    def configurate(self, dialog): # 3

        # Dialog erstellen

        return dialog # 4

Erklärungen zu den mit Nummer bezeichneten Kommentaren:

1. Um ein Plugin konfigurierbar zu machen, muss man den Parameter ``Configurable`` auf ``True`` setzen.
2. Die eigentlichen Optionen werden in einem Dictionary ``Config`` gespeichert. Der Wert ``http://www.otr-search.com/?q=`` ist somit die Standardeinstellung.
3. Ist ein Plugin konfigurierbar, **muss** auch die Methode ``configurate`` definiert werden, die OTR-Verwaltung mit einem Dialog als Parameter aufruft, wenn der Benutzer im Plugins-Dialog auf "Einstellungen" klickt.
4. Um das Anzeigen, Schließen des Dialogs kümmert sich OTR-Verwaltung.

Wird OTR-Verwaltung nun gestartet und wieder geschlossen befinden sich in der Datei ``~/.otr-verwaltung/pluginconf`` die Einträge für unser Plugin::
   
    [FindSimilar]
    server = http://www.otr-search.com/?q=

Nun muss der Dialog erstellt werden, der nur ein Textfeld umfasst, das es ermöglicht, die Suchmaschine zu ändern::

    def configurate(self, dialog):
        
        def entry_server_changed(widget, data=None): # 1
            self.Config['server'] = widget.get_text() # 2
        
        entry_server = gtk.Entry() 
        entry_server.set_text(self.Config['server']) # 3
        entry_server.connect('changed', entry_server_changed) # 4
        
        dialog.vbox.add(entry_server) # 5
    
        return dialog   

Erklärungen zu den mit Nummer bezeichneten Kommentaren:

1. Diese Funktion wird aufgerufen, wenn sich der Inhalt des Textfeldes ändert (siehe 4).
2. So wird die Option bei jeder Änderung gespeichert.
3. Das Feld wird mit dem bisherigen Wert gefüllt.
4. Textfelder stellen das Signal ``changed`` bereit. Es wird mit der oben definierten Methode verbunden.
5. Das Textfeld wird dem Dialog hinzugefügt.

Außerdem muss noch die Zeile::

    webbrowser.open("http://www.otr-search.com/?q=%s" % filename_short)

geändert werden in::

    webbrowser.open(self.Config['server'] + filename_short)

So wird der Wert schließlich auch beim Suchen genutzt.

Das Plugin ist nun fertig. Hier der komplette Code::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import gtk, re, webbrowser, os.path
    from pluginsystem import Plugin
    from constants import Section

    class FindSimilar(Plugin): 
        Name = "Ähnliche Sendungen finden"
        Desc = "Sucht bei einer Mirrorsuchmaschine nach ähnlichen Sendungen."
        Author = "Ich"
        Configurable = True
        Config = { 'server': 'http://www.otr-search.com/?q=' }
            
        def enable(self):
            self.toolbutton = self.gui.main_window.add_toolbutton(gtk.Image(), 'Ähnliche Sendungen', [Section.OTRKEY, Section.VIDEO_UNCUT])
            self.toolbutton.connect('clicked', self.find_similar_clicked) 

        def disable(self):
            self.gui.main_window.remove_toolbutton(self.toolbutton)               

        def configurate(self, dialog):
            
            def entry_server_changed(widget, data=None):
                self.Config['server'] = widget.get_text()
            
            entry_server = gtk.Entry()
            entry_server.set_text(self.Config['server'])
            entry_server.connect('changed', entry_server_changed)
            
            dialog.vbox.add(entry_server)
        
            return dialog

        def find_similar_clicked(self, widget, data=None): 
            filenames = self.gui.main_window.get_selected_filenames()

            if len(filenames) != 1:
                self.gui.message_error_box("Es muss eine Datei markiert sein.")
                return
                
            filename = os.path.basename(filenames[0])
            filename_regex = re.compile('(.*)_([0-9]{2}[\.]){2}')
            match = filename_regex.match(filename)
            filename_short = match.groups()[0]
            
            webbrowser.open(self.Config['server'] + filename_short)


Erweiterungen als Übung
#######################

* Option hinzufügen, dass der Sender (Uhrzeit, Format) beim Suchen einbezogen wird.
* Ein Bild hinzufügen (`gtk.image_new_from_file(self.get_path('bild.png'))`).  
