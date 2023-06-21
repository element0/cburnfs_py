#!/bin/bash

# install_at.sh DEST_DIR
# raygan
# Installs cburnfs module under DEST_DIR.

if (( $# < 1 )); then
    echo "Usage: $0 DEST_DIR"
    exit -1
fi

DEST_DIR=$1

if [ ! -d $DEST_DIR ]; then
    echo "$0:err: DEST_DIR not a dir"
    exit -2
fi

mkdir $DEST_DIR/cburnfs
cp cburnfs/*py $DEST_DIR/cburnfs/.
