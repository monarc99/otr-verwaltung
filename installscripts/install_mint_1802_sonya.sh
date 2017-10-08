#!/bin/bash
INSTALLDIR=${1:-"~/Software"}
INSTALLDIR=$(eval echo "$INSTALLDIR")

cleanup() {
  EXIT_CODE=$?

  case $EXIT_CODE in
    0)
      trap - 0
      echo "Script ganz durchgelaufen. Wenn nicht etwas schief ging, sollte OTR Verwaltung++ jetzt per Menü startbar sein. Manchmal taucht OTV++ erst nach einem Reset von Unity (also z.B. durch neu einloggen) im Menü auf."
      ;;
    *)
      echo "Unbekannter Fehler. Sie müssen OTRV++ manuell installieren, falls sie das Script nicht gerade selbst abgebrochen haben."
      rm ~/Downloads/master.zip
      sudo apt-get -y remove getdeb-repository
      sudo apt-add-repository -y -r ppa:mc3man/gstffmpeg-keep
      sudo add-apt-repository -y -r "deb http://old-releases.ubuntu.com/ubuntu/ wily main universe multiverse"
      ;;
  esac
  echo bitte ENTER drücken, um das Script zu beenden; read;
  exit $EXIT_CODE
}

for sig in 0 1 2 3 6 14 15; do
  trap "cleanup $sig" $sig
done

# bei Fehler abbrechen
set -e
cd ~
source /etc/lsb-release

echo "Installscript OTRV++ für Linux Mint 18.2 sonya"
echo ""
echo "Dieses Script ist nur für diese und nicht für vorherige oder zukünftige Versionen oder Derivaten gedacht."
echo "Benutzung auf eigene Gefahr."
echo ""
echo "Das Script wird die zahlreichen Abhängigkeiten von OTR installieren und benötigt root Rechte zum Installieren."
echo "Auch wird das eine oder andere Paket eine Bestätigung der EULA benötigen."
echo "Dafür muss man den OK Button per Enter Taste bestätigen. Also keine Maus"
echo "Sollte beim Bestätigen nichts passieren, ist der OK Button nicht ausgewählt. Kommt manchmal vor. Dann per TAB Taste zuerst auswählen."  

if [ "$DISTRIB_RELEASE" == "18.2" ]
  then
	# Paketliste updaten und Abhängigkeiten installieren
	sudo apt-add-repository -y ppa:mc3man/gstffmpeg-keep
	# use wily for gstreamer-ffmpeg
	sudo sed -i s/xenial/wily/ /etc/apt/sources.list.d/mc3man-gstffmpeg-keep-xenial.list
	sudo add-apt-repository -y "deb http://old-releases.ubuntu.com/ubuntu/ wily main universe multiverse"
	sudo apt-get -y update

	# unbedingt benötigte Abhängigkeiten
	sudo apt-get -y install gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly gstreamer0.10-alsa gstreamer0.10-pulseaudio python-glade2 python-libtorrent python-xdg python-gst0.10 python-dbus mplayer gstreamer0.10-ffmpeg gstreamer0.10-gnonlin


	### optionale Abhängigkeiten

        # Avidemux 2.5 cli fürs Schneiden von divx - Smartmkvmerge kann divx ebenfalls schneiden, deshalb nicht unbedingt benötigt
	# folgende Zeile mit # auskommentieren, wenn nicht benötigt
	sudo apt-get -y install avidemux-cli

	# wine für Virtualdub
	# folgende Zeile mit # auskommentieren, wenn nicht benötigt
	sudo apt-get -y install wine

	# mediainfo GUI - falls nicht benötigt
	# folgende Zeile mit # auskommentieren, wenn nicht benötigt
	sudo apt-get -y install mediainfo-gui

	# Avidemux 2.6 zum Erstellen von Cutlisten, wenn das Cutinterface nicht verwendet werden soll
	# folgende Zeilen mit # auskommentieren, wenn nicht benötigt
	wget http://archive.getdeb.net/install_deb/getdeb-repository_0.1-1~getdeb1_all.deb
	sudo dpkg -i getdeb-repository_0.1-1~getdeb1_all.deb
	rm getdeb-repository_0.1-1~getdeb1_all.deb
  sudo sed -i "s/sonya/xenial/" /etc/apt/sources.list.d/getdeb.list
	sudo apt-get update
	sudo apt-get -y install avidemux2.6-qt
	sudo apt-get -y remove getdeb-repository

	###

	# repository wieder entfernen
	sudo apt-add-repository -y -r ppa:mc3man/gstffmpeg-keep
	sudo add-apt-repository -y -r "deb http://old-releases.ubuntu.com/ubuntu/ wily main universe multiverse"
	sudo apt-get update
  else
    echo "Für diese Ubuntu Version konnte keine geeignete Abhängigkeiten gefunden werden."
    echo "OTRV++ bitte manuell installieren."
    exit -1
fi


# otrv++ laden
wget -P ~/Downloads -O ~/Downloads/master.zip https://github.com/monarc99/otr-verwaltung/archive/master.zip

# und entpacken
mkdir -p "$INSTALLDIR"
unzip -uod "$INSTALLDIR" ~/Downloads/master.zip
rm ~/Downloads/master.zip
sudo chown -R $USER "$INSTALLDIR"/otr-verwaltung-master

# Menü Eintrag erstellen
mkdir -p ~/.local/share/applications/
sed -e "/Icon=/d" "$INSTALLDIR"/otr-verwaltung-master/otrverwaltung.desktop.in > ~/.local/share/applications/otrverwaltung.desktop
echo Icon="$INSTALLDIR"/otr-verwaltung-master/data/media/icon.png >> ~/.local/share/applications/otrverwaltung.desktop

# Link auf otrverwaltung setzen

sudo ln -sf "$INSTALLDIR"/otr-verwaltung-master/bin/otrverwaltung /usr/local/bin/otrverwaltung
