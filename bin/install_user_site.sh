#!/bin/sh

USER_SITE=$(python3 -c 'import site; print(site.USER_SITE)')
DEST=${USER_SITE}/cburnfs

BLACKSTRAP_SRC=cburnfs/blackstrap.py
BLACKSTRAP_DEST=${USER_SITE}/blackstrap.py

if [ ! -e $USER_SITE ]
then
    mkdir -p $USER_SITE
    echo created dir $USER_SITE
fi


cp -R cburnfs ${DEST}
cp ${BLACKSTRAP_SRC} ${BLACKSTRAP_DEST}


if [ -e ${DEST} ]
then
    echo installed cburnfs at ${DEST}
else
    echo error. cburnfs not installed at ${DEST}
fi


if [ -e ${BLACKSTRAP_DEST} ]
then
    echo installed blackstrap at ${BLACKSTRAP_DEST}
else
    echo error. blackstrap not installed at ${BLACKSTRAP_DEST}
fi
