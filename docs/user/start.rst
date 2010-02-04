Einstieg
========

Installation
############

Es muss mindestens ein Schnittprogramm installiert sein: *Avidemux* lässt sich über die Paketverwaltung installieren. *VirtualDub*, das für HQ-Dateien erforderlich ist, muss mit Hilfe von Wine laufen, das Windows-Programme unter Linux ausführen kann:

1. Zunächst muss `Wine <http://www.winehq.org/download/>`_ in einer aktuellen Version (mind. 1.1.14) installiert werden.
2. Anschließend muss `Virtualdub <http://sourceforge.net/project/showfiles.php?group_id=9649&package_id=9727&release_id=576135>`_ heruntergeladen werden und an einem geeigneten Ort entpackt werden.
3. Da Virtualdub Codecs benötigt, muss man `ffdshow <http://sourceforge.net/projects/ffdshow-tryout/files/Old%20releases/generic%20builds/ffdshow_beta5_rev2033_20080705_clsid.exe/download>`_ installieren.

.. note:: 
  Nicht alle Kombinationen von VirtualDub und ffdshow funktionieren! 
  
  * Empfehlung: beta4 oder beta5, *nicht* beta6
  * VirtualDub: 1.7.8, vor allem, wenn die Datei auch auf Hardware-Playern abgespielt werden soll.

  Monarc99 hat dazu einen sehr hilfreichen `Beitrag im OTR-Forum <http://www.otrforum.com/showpost.php?p=247925&postcount=56>`_ verfasst.

Empfohlen wird außerdem der MPlayer, der für viele Funktionen erforderlich ist und ebenfalls über die Paketverwaltung verfügbar ist (Wer HQ/HD-Dateien schneidet, *muss* den MPlayer installieren).

Unter debian-basierten Distributionen (z.B. Ubuntu): ``sudo apt-get install avidemux mplayer``

Anschließend kann von der `Download-Seite ein deb- oder rpm-Paket heruntergeladen <http://code.google.com/p/otr-verwaltung/downloads/list>`_ werden, dass sich einfach über einen Doppelklick installieren lässt. Dabei werden auch Python, GTK und PyGTK, falls diese Pakete noch nicht vorhanden sein sollten, installiert.

Konfigurieren
#############

* *Normale avi-Dateien* können mit Avidemux (empfohlen) oder Virtualdub geschnitten werden. Um Dateien mit Cutlisten ohne Oberfläche zu schneiden, kann man auch avidemux2_cli installieren.
* *HQ/HD-Dateien* sollten immer mit Virtualdub geschnitten werden.

Beste Einstellungen:

+--------+--------------------------------+---------------------------+
|        |  mit Cutlist                   | manuell                   |
+--------+--------------------------------+---------------------------+
| avi    |  avidemux *oder* avidemux2_cli | avidemux                  |
+--------+--------------------------------+---------------------------+
| HQ/HD  |  /pfad/zu/vdub.exe             | /pfad/zu/VirtualDub.exe   |
+--------+--------------------------------+---------------------------+

.. note:: Die genauen Programmnamen können variieren!

.. note:: Wird avidemux2_cli benutzt, **müssen** :ref:`die Abfragen von Avidemux abgeschaltet werden <nachfragen_avidemux>`.

Funktionen
##########

Die folgende Liste von Funktionen ist noch unvollständig.

Videos schneiden
++++++++++++++++

Es lasst sich Videos auf fünf Arten schneiden:

=================================  ==============
Nachfragen                         Die unteren vier Möglichkeiten werden bei jeder Datei abgefragt.
Beste Cutlist                      Das Programm wählt die beste der heruntergeladenen Cutlisten auf Basis der Benutzerbewertungen und der Wertung des Autors aus.

Cutlist wählen                     Die Cutlisten werden heruntergeladen und der Benutzer wählt bei jeder Datei die Cutlist aus
Lokale Cutlist                     Es wird im Ordner der Video-Datei nach einer Cutlist gesucht.

Manuell (und Cutlist erstellen)    Das Schnittprogramm wird geöffnet, damit der Benutzer die Datei selber schneiden kann. Optional kann auch eine Cutlist erstellt werden.
=================================  ==============

Cutlisten erstellen
+++++++++++++++++++

Die Datei muss im *manuellen Modus* geschnitten werden. Je nach Einstellung öffnet sich dann Avidemux oder VirtualDub.

**Mit Avidemux:**

  * Bearbeiten Sie die Datei wie gewünscht (`Anleitung im otrforum <http://www.otrforum.com/showpost.php?p=211693&postcount=3>`_).
  * Beenden Sie Avidemux. Die Datei wird nun geschnitten.
  * In der Zusammenfassung können Sie Einstellungen für die Cutlist vornehmen.

**Mit VirtualDub:**

  * Bearbeiten Sie die Datei wie gewünscht.
  * Wählen Sie den Menüpunkt :menuselection:`File --> Save processing settings`.
  * **Klicken Sie den Haken vor "Include selection and edit list" an**. Gehen Sie zum Ordner, in dem sich auch die ungeschnittene Video-Datei befindet. Speichern sie die Datei als ``cutlist.vcf`` ab.
  * Beenden Sie VirtualDub. Die Datei wird nun geschnitten.
  * In der Zusammenfassung können Sie Einstellungen für die Cutlist vornehmen.

