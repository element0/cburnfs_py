# Cloudburner FS

Cloudburner FS (CburnFS) is a multi-layer, overlay file-system, whereeach layer originates from anywhere on the network or localhost.

Each layer can be written to. CburnFS tracks which files belong to which layer, syncs files which are shared between layers, and keeps other files separate.

The layers are defined from `cburnfs` entries in an `fstab` file.

## Usage Example

	from cburnfs import CBurnFS
	from cburnfs import demo_blackstrap_config
	cbfs = CBurnFS("file://fs.localhost")

	cbfs.listdir("/")


## About BlackstrapFS

When deveoping on the iPhone version of Jupyter notebooks (Carnets), 'file://' style URL's are relative to the sandboxed instance of the app, and change over successive app sessions. So BlackstrapFS maps a file system path to a file:// style URL and proxies the file service.

Url's must be mapped in advance to BlackstrapFS `shares` before initializing the CBurnFS file-system object.

	see demo_blackstrap_config.py

Once proxied, CburnFS can be initialized, and any file:// URL's used in the `fstab` file will be derived from the BlackstrapFS share names.



## Dev Environment

*DO NOT EDIT THE PYTHON FILES DIRECTLY*

The main source files are Jupyter Notebooks (ipynb) files.

There is a `Make from Notebooks.ipynb` which generates the python files.


## INSTALLATION

The Dockerfile puts the `cburnfs` python package into the `site.USER_SITE` location.


## TODO

- Use `pip` to install into a system-wide location.


