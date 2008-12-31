#!/bin/sh

name='otr-verwaltung';
version='0.2';

mv src "$name-$version";
tar czvf "$name-$version.orig.tar.gz" "$name-$version"/ --exclude=.svn --exclude=.* --exclude=*~ --exclude=screenshots;
mv "$name-$version" src;

tar -xf "$name-$version.orig.tar.gz"


#cd otr-verwaltung-0.2
#dh_make -e elbersb@gmail.com -f ../otr-verwaltung-0.2.orig.tar
#cd debian
#rm *.ex *.EX README.debian
