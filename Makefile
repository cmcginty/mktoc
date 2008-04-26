# mktoc // (c) 2008 Patrick C. McGinty
# mktoc[@]tuxcoder[dot]com
#

NAME=mktoc
VER=1.0
DIST_DIR=dist
TAR=${DIST_DIR}/${NAME}-${VER}.tar.gz
SRC_DIR=${DIST_DIR}/${NAME}-${VER}

install:
	python setup.py install

pydist: Makefile
	python setup.py sdist

pydist-test:
	tar xzf ${TAR} -C ${DIST_DIR}
	sudo make -C ${SRC_DIR} install
	sudo rm -rf ${SRC_DIR}

dist: release
release: pydist pydist-test

test:
	src/alltests.py

