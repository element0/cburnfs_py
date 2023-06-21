import sys
sys.path.append('lib')
from cburnfs.CBurnFS import CBurnFS
from cburnfs.ApathRootCosm import apathRootCosm
from fs import open_fs

def cburnfs_from_dir(basepath,hostname='localhost',bootshare='boot'):
    blackstrapfs = apathRootCosm['services']['file']
    blackstrapfs.initHost(hostname)
    basedir = open_fs(basepath)
    for each in basedir.listdir('/'):
        blackstrapfs.addShare(f'{basepath}/{each}',each)

    cbfs = CBurnFS(f'file://{bootshare}.{hostname}')
    return cbfs

