from fs.base import FS
from fs.info import Info
import six
from fs.errors import ResourceNotFound
from mergeinfo import mergeinfo

def mergehostinfo(A,B,out=None):
    pass

class MulticelFS(FS):
    def __init__(self, dcels):
        super().__init__()
        self.dcels = dcels
        
    def _close(self):
        #todo: close constituents?
        #for ea in self.dcels:
            #ea.service.close()
        # causing trouble
        pass
        
    if six.PY2:
        def close(self):  # noqa: D102
            self._close()
            super(MultiCelFS, self).close()
    else:
        def close(self): # noqa: D102
            self._close()
            super().close()
        
    def getinfo(self, path, namespaces=None):
        raw = dict()
        for ea in self.dcels:
            try:
                i2 = ea.getinfo(path,namespaces)
                raw = mergeinfo(raw,i2.raw)
                try:
                    # hostname = ea.service.url.netloc
                    hostname = ea.service._dcel_url
                    hostinfo = { 'hosts': [hostname] }
                    raw = mergeinfo(raw, hostinfo)
                except:
                    pass
            except ResourceNotFound:
                pass
        if raw == dict():
            raise ResourceNotFound(path)
            i = None
        else:
            i = Info(raw)
        return i
    
    def geturl(self,path):
        return None
    
    def listdir(self,path): # Get a list of resources in a directory.
        lsprep = set()
        for ea in self.dcels:
            try:
                lsprep.update(
                    ea.listdir(path)
                )
            except ResourceNotFound:
                pass
        return list(lsprep)
    
    def makedir(self,path, permissions=None, recreate=False): # Make a directory.
        subpath = ""
        return SubFS(self,subpath)
    
    def openbin(self,
                path,
                mode='r',
                buffering=-1,
                **options):
        for ea in self.dcels:
            try:
                res = ea.openbin(
                    path,
                    mode,
                    buffering
                )
            except ResourceNotFound:
                pass
        # Open a binary file.
        return res
    
    def remove(self,path):
        """TBD: Remove a file."""
        return 
    
    def removedir(self,path):
        """TBD: Remove a directory."""
        pass
    
    def setinfo(self,path,info):
        """TBD: Set resource information."""
        pass
    
    #######################################
    # NON-PYFILESYSTEM-CONFORMANT METHODS #
    #######################################
    #
    # non-FS API specific to MultiCelFS
    #
    # TODO: factor as many of these out as possible.
    
    def add_dcel(self, dcel):
        self.dcels.append(dcel)
        
    def remove_dcel(self, dcel):
        self.dcels.remove(dcel)
        
    def get_dcel_by_host(self,hostname):
        for each in self.dcels:
            hostid = each.getinfo('/').raw['hosts'][0]
            if hostid == hostname:
                return each
        return None