#!/bin/bash

cleanup() {
  EXIT_CODE=$?
  
  case $EXIT_CODE in
    0)
      trap - 0
      echo "Script ganz durchgelaufen. Wenn nicht etwas schief ging, sollte OTR Verwaltung++ jetzt per Menü startbar sein. Manchmal taucht OTV++ erst nach einem Reset von Unity (also z.B. Reboot) im Menü auf."
      ;;
    *)
      echo "Unbekannter Fehler. Sie müssen OTRV++ manuell installieren, falls sie das Script nicht gerade selbst abgebrochen haben."
      rm ~/Downloads/master.zip
      sudo apt-get -y remove getdeb-repository
      sudo apt-add-repository -y -r ppa:mc3man/gstffmpeg-keep
      sudo add-apt-repository -y -r "deb http://de.archive.ubuntu.com/ubuntu/ wily main universe multiverse"
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
INSTALLDIR="Software"
source /etc/lsb-release

echo "Installscript OTRV++ für Ubuntu 16.04 Xerius"
echo ""
echo "Dieses Script ist nur für Ubuntu 16.04 und nicht für vorherige oder zukünftige Ubuntu Versionen oder Derivaten gedacht."
echo "Benutzung auf eigene Gefahr."
echo ""
echo "Das Script wird die zahlreichen Abhängigkeiten von OTR installieren und benötigt root Rechte zum Installieren."
echo "Auch wird das eine oder andere Paket eine Bestätigung der EULA benötigen."
echo "Dafür muss man den OK Button per Enter Taste bestätigen. Also keine Maus"
echo "Sollte beim Bestätigen nichts passieren, ist der OK Button nicht ausgewählt. Kommt manchmal vor. Dann per TAB Taste zuerst auswählen."  

if [ "$DISTRIB_RELEASE" == "16.04" ]
  then
	# Paketliste updaten und Abhängigkeiten installieren
	wget http://archive.getdeb.net/install_deb/getdeb-repository_0.1-1~getdeb1_all.deb
	sudo dpkg -i getdeb-repository_0.1-1~getdeb1_all.deb
	sudo apt-add-repository -y ppa:mc3man/gstffmpeg-keep
	# use wily for gstreamer-ffmpeg
	sudo sed -i s/xerius/wily/ /etc/apt/sources.list.d/mc3man-ubuntu-gstffmpeg-keep-xenial.list
	sudo add-apt-repository -y "deb http://de.archive.ubuntu.com/ubuntu/ wily main universe multiverse"
	sudo apt-get -y update

	sudo apt-get -y install avidemux-cli gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly gstreamer0.10-alsa python-glade2 python-libtorrent wine mediainfo-gui python-xdg python-gst0.10 python-dbus avidemux2.6-qt mplayer gstreamer0.10-ffmpeg gstreamer0.10-gnonlin

	sudo apt-get -y remove getdeb-repository
	sudo apt-add-repository -y -r ppa:mc3man/gstffmpeg-keep
	sudo add-apt-repository -y -r "deb http://de.archive.ubuntu.com/ubuntu/ wily main universe multiverse"
  else
    echo "Für diese Ubuntu Version konnte keine geeignete Abhängigkeiten gefunden werden."
    echo "OTRV++ bitte manuell installieren."
    exit -1
fi


# otrv++ laden
wget -P ~/Downloads https://github.com/monarc99/otr-verwaltung/archive/master.zip

# und entpacken
mkdir -p ~/"$INSTALLDIR"
unzip -uod ~/"$INSTALLDIR" ~/Downloads/master.zip
rm ~/Downloads/master.zip

# Menü Eintrag erstellen
mkdir -p ~/.local/share/applications/
sed -e "/Icon=/d" ~/"$INSTALLDIR"/otr-verwaltung-master/otrverwaltung.desktop.in > ~/.local/share/applications/otrverwaltung.desktop
echo Icon=$(eval echo ~)/"$INSTALLDIR"/otr-verwaltung-master/data/media/icon.png >> ~/.local/share/applications/otrverwaltung.desktop

# Link auf otrverwaltung setzen

sudo ln -sf $(eval echo ~)/"$INSTALLDIR"/otr-verwaltung-master/bin/otrverwaltung /usr/local/bin/otrverwaltung
