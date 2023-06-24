# Cloudburner FS

Cloudburner FS (`CBurnFS`) is a multi-layer, overlay file-system, where each layer originates from anywhere on the network.

CburnFS tracks which files belong to which layer, syncs shared files between layers, and keeps other files separate.

Layers are defined from `cburnfs` entries in an `fstab` file in a boot filesystem.


## Usage

The easiest way to try it out:
    
    1) create a directory holding different mounted file systems.

    ../mounts/
        boot/
        fs2/
        fs3/

    2) create a fstab file in the boot filesystem under '@/etc'.

    mounts/boot/@/etc/fstab

    ...

    file://boot.localhost   /   user,shortid=boot   0   0
    file://fs2.localhost    /   user,shortid=fs2    0   0
    file://fs3.localhost    /   user,shortid=fs3    0   0

    3) create a library directory, such as 'lib' or whatever,
       and install cburnfs into it.

    mkdir $LIB_LOCATION
    cd $CBURN_GIT_ROOT
    ./bin/install_at.sh $LIB_LOCATION 


    4) in python

    import sys; sys.path.append(LIB_LOCATION_HERE)
    from cburnfs.cburnfs_tools import cburnfs_from_dir
    cbfs = cburnfs_from_dir('mounts','localhost','boot')
    cbfs.listdir('/')

    =) you should see a listing of the filesystems combined.


## Python Imports Caveat

Due to the hack-ishly cobbled together `cburnfs` module,
if you want to use the subcomponents -- which you will want to do! -- then you have to import them thusly:

    import cburnfs.Dcel
    import cburnfs.APath
    import cburnfs.Fudge
    from Dcel import Dcel
    from APath import APath
    from Fudge import Fudge

Looks shitty, but turns out smooth. There are dependencies between the components, which have knowledge of each other but not of the cburnfs module. The above imports will mean that type(Dcel) will evaluate the same inside your code as is does inside the APath and Fudge classes -- critical since each class wraps the other.

    a = Dcel(service,address)
    b = APath(a)
    c = Fudge(b)

(tested in Python 3.11.3)


## About BlackstrapFS

When developing on iPhone using Jupyter notebooks (Carnets), 'file://' style URL's are relative to the sandboxed instance of the app, and change over repeated app sessions. BlackstrapFS maps a file system path to a file:// style URL and proxies the file service.

    file://boot.localhost

Url's must be mapped in advance to BlackstrapFS `shares` before initializing the CBurnFS file-system object.

	see `demo_blackstrap_config.py`

Once proxied, CburnFS can be initialized, and `file://` URL's used in the `fstab` file will map to BlackstrapFS share names.



## Dev Environment

*DO NOT EDIT THE PYTHON FILES DIRECTLY*

The main source files are Jupyter Notebooks (ipynb) files.

There is a `Make from Notebooks.ipynb` which generates the python files.


## INSTALLATION

The Dockerfile puts the `cburnfs` python package into the `site.USER_SITE` location.




