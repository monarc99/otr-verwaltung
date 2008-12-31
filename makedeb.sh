#!/bin/sh

name='otr-verwaltung';
version='0.2';

rm $name-$version.orig.tar.gz
rm -r $name-$version

mv src "$name-$version";
tar czvf $name-$version.orig.tar.gz $name-$version --exclude=*.pyc --exclude=.svn --exclude=.* --exclude=*~ --exclude=screenshots;
mv "$name-$version" src;

tar -xf $name-$version.orig.tar.gz;

cd $name-$version
dh_make -e elbersb@gmail.com
rm ../$name-$version.orig.tar.gz

cd debian
rm *.ex *.EX README.Debian

# Fill files

cat > control << EOF
Source: otr-verwaltung
Section: misc
Priority: optional
Maintainer: Benjamin Elbers <elbersb@gmail.com>
Build-Depends: debhelper (>= 7)
Standards-Version: 3.7.3
Homepage: <insert the upstream URL, if relevant>

Package: otr-verwaltung
Architecture: all
Depends: 
Description: Manages otrkeys and avis from onlinetvrecorder.com
 Manages otrkeys and avis from onlinetvrecorder.com
 Feature list:
    -
    -
EOF

cp ../../rules rules

cat > dirs << EOF
/usr/bin
/usr/share/applications
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

The Debian packaging is (C) 2008, benjamin <elbersb@gmail.com> and
is licensed under the GPL, see /usr/share/common-licenses/GPL.
EOF

cd ..

cat >> otr-verwaltung.desktop << EOF
[Desktop Entry]
Encoding=UTF-8
Name=OTR-Verwaltung
Exec=otrverwaltung
Icon=
Comment=Verwalten von otrkey- und avi-Dateien von onlinetvrecorder.com
Type=Application
Categories=AudioVideo;
EOF

dpkg-buildpackage   
