#!/bin/bash
INSTALLDIR=${1:-"~/Software"}
INSTALLDIR=$(eval echo "$INSTALLDIR")

cleanup() {
  EXIT_CODE=$?

  case $EXIT_CODE in
    0)
      trap - 0
      echo "Skript ganz durchgelaufen. Wenn nicht etwas schief ging, sollte OTR Verwaltung++ jetzt per Menü startbar sein. Manchmal taucht OTV++ erst nach einem Reset von Cinnamon (also z.B. durch neu einloggen) im Menü auf."
      ;;
    *)
      echo "Unbekannter Fehler. Sie müssen OTRV++ manuell installieren, falls sie das Skript nicht gerade selbst abgebrochen haben."
      uninstall_repos;
      ;;
  esac
  echo "Bitte ENTER drücken, um das Skript zu beenden"; read;
  exit $EXIT_CODE
}

uninstall_repos() {
	rm -f /etc/apt/sources.list.d/gstffmpeg-keep.list
    apt-key del ED8E640A
	add-apt-repository -y -r "deb http://old-releases.ubuntu.com/ubuntu/ wily main universe multiverse"
	apt-get update
}


if [ $UID -ne 0 ]; then
    echo "Abbruch: Dieses Skript muss als root ausfeührt werden."
    exit 255
fi


for sig in 0 1 2 3 6 14 15; do
  trap "cleanup $sig" $sig
done

# bei Fehler abbrechen
set -e
cd ~
source /etc/lsb-release

echo "Installscript OTRV++ für Linux Mint 19.1 Tessa"
echo ""
echo "Dieses Script ist nur für diese und nicht für vorherige oder zukünftige Versionen oder Derivaten gedacht."
echo "Benutzung auf eigene Gefahr."
echo ""
echo "Das Script wird die zahlreichen Abhängigkeiten von OTR installieren und benötigt root Rechte zum Installieren."
echo "Auch wird das eine oder andere Paket eine Bestätigung der EULA benötigen."
echo "Dafür muss man den OK Button per Enter Taste bestätigen. Also keine Maus"
echo "Sollte beim Bestätigen nichts passieren, ist der OK Button nicht ausgewählt. Kommt manchmal vor. Dann per TAB Taste zuerst auswählen."

if [ "$DISTRIB_DESCRIPTION" == "Linux Mint 19.1 Tessa" ]
  then
	# Paketliste updaten und Abhängigkeiten installieren
    cat <<'EOF' > /etc/apt/sources.list.d/gstffmpeg-keep.list
# This file includes the gstffmpeg ppa used by OTR-Verwaltung

deb http://ppa.launchpad.net/mc3man/gstffmpeg-keep/ubuntu wily main
EOF
    # Installiere passenden key:
    sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com ED8E640A
	# use wily for gstreamer-ffmpeg
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
	sudo apt-get -y install wine-stable winetricks

	# mediainfo GUI - falls nicht benötigt
	# folgende Zeile mit # auskommentieren, wenn nicht benötigt
	sudo apt-get -y install mediainfo-gui

	# Avidemux 2.7.x zum Erstellen von Cutlisten, wenn das Cutinterface nicht verwendet werden soll
	# folgende Zeilen mit # auskommentieren, wenn nicht benötigt
	sudo apt-get -y install avidemux-qt


	###

	# repository wieder entfernen
    uninstall_repos;

  else
    echo "Für diese Linux-Version konnte keine geeignete Abhängigkeiten gefunden werden."
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
