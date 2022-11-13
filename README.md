# Cloudburner FS

This filesystem does heavy lifting for laydbug.io.

Cloudburn FS (CBurnFS) reads `cburnfs` entries from an `fstab` file and produces an overlay file system.

Each layer in the filesystem can be written to. CBurnFS tracks which files belong to which layer, syncs files which are shared between layers, and keeps other files separate.

CBurnFS provides methods for moving/duping files between layers.

## Dev Environment

The main source files are Jupyter Notebooks (ipynb) files.

*DO NOT EDIT THE PYTHON FILES DIRECTLY*

There is a `Make from Notebooks.ipynb` which generates the python files.
