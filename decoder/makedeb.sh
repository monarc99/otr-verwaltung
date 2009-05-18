#!/bin/sh

name='otrdecoder';
version='518';

mkdir $name-$version
cp otrdecoder $name-$version
cd $name-$version

dh_make -f otrdecoder
cd debian

# Fill files
cat > control << EOF
Source: otrdecoder
Section: misc
Priority: optional
Maintainer: Benjamin Elbers <elbersb+otr@gmail.com>
Build-Depends: debhelper (>= 7)
Standards-Version: 3.7.3
Homepage: <insert the upstream URL, if relevant>

Package: otrdecoder
Architecture: all
Depends: 
Description: Dekodiert otrkey-Dateien von onlinetvrecorder.com
EOF


cat > rules << EOF 
#!/usr/bin/make -f
# -*- makefile -*-

configure: configure-stamp
configure-stamp:
	dh_testdir
	# Add here commands to configure the package.

	touch configure-stamp


build: build-stamp

build-stamp: configure-stamp  
	dh_testdir

	touch \$@

clean: 
	dh_testdir
	dh_testroot
	rm -f build-stamp configure-stamp

	dh_clean 

install: build
	dh_testdir
	dh_testroot
	dh_clean -k 
	dh_installdirs

	cp otrdecoder \$(CURDIR)/debian/otrdecoder/usr/bin/otrdecoder


# Build architecture-independent files here.
binary-indep: build install
# We have nothing to do by default.

# Build architecture-dependent files here.
binary-arch: build install
	dh_testdir
	dh_testroot
	dh_installchangelogs 
	dh_installdocs
	dh_installexamples
	dh_installman
	dh_link
	dh_strip
	dh_compress
	dh_fixperms
	dh_installdeb
	dh_shlibdeps
	dh_gencontrol
	dh_md5sums
	dh_builddeb

binary: binary-indep binary-arch
.PHONY: build clean binary-indep binary-arch binary install configure
EOF

cat > dirs << EOF
/usr/bin
EOF

rm README.Debian   
rm copyright

cd ..

dpkg-buildpackage   

cd ..
rm -r $name-$version
rm ${name}_${version}-1.dsc
rm ${name}_${version}-1.tar.gz
rm ${name}_${version}-1_i386.changes

sudo alien -r ${name}_${version}-1_all.deb
