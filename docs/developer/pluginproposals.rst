Vorschläge für Plugins
======================

Ein paar Ideen...

Videos aneinanderfügen
######################

Beim Klick auf "Videos aneinanderfügen" öffnet sich ein Fenster, in das per Drag and Drop Videos gezogen werden können. Mit Schaltflächen im Fenster kann man Videos wieder entfernen und die Reihenfolge verändern. Beim Klick auf Speichern wird eine neue Datei unter einem gewählten Namen mit Hilfe von Avidemux/VirtualDub gespeichert.

Downloads verifizieren
######################

Bei unvollständig heruntergeladenen Dateien kann man Torrents benutzen, um die otrkeys zu reparieren. 

Die Dateinamen der Torrents sind immer gleich aufgebaut:

Link: `http://81.95.11.2/xbt/xbt_torrent_create.php?filename=DATEINAME&userid=USERID&mode=free&hash=PASSWORDHASH&user=pass`

Man benötigt: ID-des Users (sollte in den Einstellungen des Plugins gespeichert werden), den MD5-Hash des Passworts (kann aus den OTR-Verwaltung-Einstellungen generiert werden) und den Dateinamen.

Ein Kommandozeilen-Programm für Torrents ist **aria2c**:

`aria2c --check-integrity=true --continue  --enable-dht --max-overall-upload-limit=12K  --listen-port=6881-6889 --bt-hash-check-seed=false --follow-torrent=mem "Link"`

Obige Zeile läd die Torrent Datei in den Speicher, prüft die schon heruntergeladene Datei und lädt sie vollständig bzw. korrigiert sie, indem sie vom Torrentnetzwerk zuende lädt.

Quelle: http://www.otrforum.com/showpost.php?p=248030&postcount=58

Filtersystem
############

.. note:: Ein *automatisches* Verschieben nach dem Schneiden wäre im Moment nicht zu realisieren. Falls sich jemand dieses Plugins annimmt, würde ich eine entsprechende Möglichkeit in OTR-Verwaltung einbauen.

Zitat:
    
    "Ich trenne gerne Serien von Filmen und hab jeweils auch meine Unterordner. Verschieben muss ich das Ganze dann leider noch manuell. Ähnlich wie bei E-Mail-Programmen könnte man dann doch z.B. einstellen, dass Dateien mit einer gewissen Zeichenfolge auch in einen bestimmten Ordner verschoben werden."

Quelle: http://www.otrforum.com/showpost.php?p=254879&postcount=98

Erweiterung MKV-Plugin
######################

Da OTR bei manchen Aufnahmen mit einem falschen Seitenverhältnis aufnimmt, könnte man das MKV-Plugin um die Möglichkeit erweitern, das neue, korrekte Seitenverhältnis pro Datei einzustellen.

Es gilt aber zu bedenken:

    "Jetzt ist bloß die Frage, sollte man das wirklich alles in deine otrverwaltung einbauen. mkvmerge hat eine GUI, wo man das alles einstellen kann. Also ob es ab einen bestimmten Punkt nicht einfach sinnvoller ist, die GUI von mkvmerge zu starten."

Quelle: http://www.otrforum.com/showpost.php?p=254812&postcount=95

Umwandlung in iPod-Format
#########################

Bei DivX-Aufnahmen muss nur die Audiospur in AAC umgewandelt werden. Dies kann automatisiert mit Avidemux geschehen:

``app.audio.codec("aac",128,4,"80 00 00 00 ");``

Zum automatischen Übertragen der Datei kann libgpod (Python-Bindings) benutzt werden.

