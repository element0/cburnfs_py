# Cloudburner FS

Cloudburner FS (`CBurnFS`) is a multi-layer, overlay file-system, where each layer originates from anywhere on the network.

CburnFS knows which files belong to which layer, syncs shared files between layers, and keeps other files separate.

Layers are defined from `cburnfs` entries in an `fstab` file in a boot filesystem.


## Metadata

Metadata is kept in a `cburnfs-meta` filesystem, also with a corresponding entry in the `fstab` file. The meta filesystem is designed to work with a redis backend. The `spec` field of the `fstab` defines the name and (optional) port of the redis host. IMPORTANT: If you do not run a redis host, simply do not install `redis` in your python environment. *If* you *do* install `redis` you will be required to run the redis host *before* creating the `CBurnFS` instance, and you will be responsible for making sure the redis host is secure and available on the same network as your CBurnFS. (A pain in the arse if you are just experimenting with CBurnFS.)


## Editing this Repo

Do not edit the .py files directly. The .ipynb files are the masters. The masters can be edited with Jupyter Notebooks or Carnets (a Jupyter Notebooks implementation on iOS). The benefits of using Jupyter Notebooks are that documentation and unit tests will be stored in the same notebook as the main source code.

The source code must *always* be cell number 2.

Use the notebook `Make from Notebooks.ipynb` to extract the source code into python files.

Of course, you will eventually tire of the GUI. So to edit with vim:

    source _venv/bin/activate
    pip3 install jupytext
    mkdir -p ~/.vim/plugin && \
    curl https://raw.githubusercontent.com/goerz/jupytext.vim/master/plugin/jupytext.vim ~/.vim/plugin/jupytext.vim


## Usage

The easiest way to try it out:
    
    1) create a directory holding different mounted file systems.

    ../mountpoints/
        boot/
        fs2/
        fs3/

    2) create a fstab file in the boot filesystem under '@/etc'.

    mounts/boot/@/etc/fstab

    ...

    file://boot.localhost   /   user,shortid=boot   0   0
    file://fs2.localhost    /   user,shortid=fs2    0   0
    file://fs3.localhost    /   user,shortid=fs3    0   0
    metafs-backend   no-mount   nouser,userid=me@example.com,userhome=me-home,userurl=me-home.example.com    0  0

    3) create a library directory, such as 'lib' or whatever,
       and install cburnfs into it.

    mkdir $LIB_LOCATION
    git clone https://github.com/element0/cburnfs_py $CBURN_GIT_ROOT
    cd $CBURN_GIT_ROOT
    ./bin/install_at.sh $LIB_LOCATION 


    4) in python

    import sys; sys.path.append(LIB_LOCATION)
    from cburnfs.cburnfs_tools import cburnfs_from_dir
    cbfs = cburnfs_from_dir('mountpoints')
    cbfs.listdir('/')

    =) you should see a listing of the filesystems combined.


## Python Imports Caveat

Due to the hurridly cobbled together `cburnfs` module,
if you want to use the subcomponents then you have to import them like this:

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

Also, this *should* keep the dependencies inside the Jupyter Notebooks files from breaking.


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




