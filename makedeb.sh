#!/bin/sh

name='otr-verwaltung';
version=`cat src/VERSION`;

rm $name-$version.orig.tar.gz
rm -r $name-$version

mv src "$name-$version";
tar czvf $name-$version.orig.tar.gz $name-$version --exclude=*.pyc --exclude=.git --exclude=.* --exclude=*~ --exclude=screenshots --exclude=log --exclude=conf;
mv "$name-$version" src;

tar -xf $name-$version.orig.tar.gz;

cd $name-$version

cp ../README.md README

dh_make -e elbersb@gmail.com
rm ../$name-$version.orig.tar.gz

cd debian
rm *.ex *.EX README.Debian

# Fill files

cat > control << EOF
Source: otr-verwaltung
Section: misc
Priority: optional
Maintainer: Benjamin Elbers <elbersb+otr@gmail.com>
Build-Depends: debhelper (>= 7)
Standards-Version: 3.7.3
Homepage: <insert the upstream URL, if relevant>

Package: otr-verwaltung
Architecture: all
Depends: python-gtk2
Description: Dateien von onlinetvrecorder.com verwalten:
    - otrkey-Dateien dekodieren
    - avi-Dateien (DivX und HQ) mit Cutlists schneiden (Avidemux und Virtualdub, auch unter Linux!)
    - Cutlists nach dem Schneiden bewerten
    - avi-Dateien mit Hilfe von EDL-Dateien geschnitten abspielen
    - Schnitte vorher mit dem Mplayer betrachten
    - Viele Dateien gleichzeitig verarbeiten
    - u. v. m.
EOF

cp ../../rules rules

cat > dirs << EOF
/usr/bin
/usr/share/applications
/usr/share/icons
EOF

cat > copyright << EOF
This package was debianized by benjamin <elbersb@gmail.com> on
Wed, 31 Dec 2008 18:07:07 +0100. 

Upstream Author(s):

    Benjamin Elbers <elbersb@gmail.com>

Copyright:

    Copyright (C) 2008 Benjamin Elbers
    
License:

    GPL v3

The Debian packaging is (C) 2009, Benjamin Elbers <elbersb@gmail.com> and
is licensed under the GPL, see /usr/share/common-licenses/GPL.
EOF

cd ..

cat >> otr-verwaltung.desktop << EOF
[Desktop Entry]
Encoding=UTF-8
Name=OTR-Verwaltung
Exec=otrverwaltung
Icon=/usr/share/icons/hicolor/48x48/apps/otrverwaltung.png
Comment=Verwalten von otrkey- und avi-Dateien von onlinetvrecorder.com
Type=Application
Categories=AudioVideo;
EOF

dpkg-buildpackage   

cd ..
rm -r $name-$version

echo "DO: sudo alien -r x.deb"
