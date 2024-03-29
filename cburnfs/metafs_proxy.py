from metafs import MetaFS
from fs.base import FS
from fs.path import split as path_split
from fs.info import Info
from fs.errors import ResourceNotFound


class MetaFSProxy(FS):

    def __init__(self, targetfs, metafs):
        self.targetfs = targetfs
        self.metafs = metafs

        super().__init__()

    def close(self):
        try:
            self.targetfs.close()
        except:
            pass
        try:
            metafs.close()
        except:
            pass
        super().close()

    def getinfo(self, path, namespaces=None):
        i = self.targetfs.getinfo(path,namespaces).raw
        try:
            i2 = self.metafs.getinfo(path,namespaces).raw
        except ResourceNotFound:
            i2 = dict() 
        i2.update(i)
        _dirname, _basename = path_split(path)
        self.metafs.makedirs(_dirname)
        self.metafs.makeinode(path)
        self.metafs.setinfo(path, i2)
        return Info(i2)

    def setinfo(self, path, info_raw):
        self.targetfs.setinfo(path, info_raw)
        _dirname, _basename = path_split(path)
        self.metafs.makedirs(_dirname)
        self.metafs.makeinode(path)
        self.metafs.setinfo(path, info_raw) 

    def makedir(self, path, permissions=None, recreate=False):
        self.targetfs.makedir(path, permissions, recreate)
        _dirname, _basename = path_split(path)
        self.metafs.makedirs(_dirname)
        self.metafs.makedir(path, permissions, recreate)

    def listdir(self, path):
        """Very immature. Only adds inodes.
        Does not remove missing nodes.
        Relies on metafs to remain in sync via 'remove()'
        and 'removedir()' methods."""
        elements = self.targetfs.listdir(path)
        for filename in elements:
            childpath = f'{path}/{filename}'
            self.metafs.makeinode(childpath)
        return elements

    def openbin(self, path, mode='r', buffering=-1, **options):
        return self.targetfs.openbin(path, mode, buffering, **options)

    def remove(self, path):
        self.targetfs.remove(path)
        self.metafs.remove(path)

    def removedir(self, path):
        self.targetfs.removedir(path)
        self.metafs.removedir(path)

