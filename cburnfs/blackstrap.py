from fs.osfs import OSFS
from fs.errors import CreateFailed
from socket import gethostname
from urllib.parse import urlparse
import six



"""
0.3
changed: initClass() --> initHost(name)
changed: addShare() removed hostname
changed: __init__() use url to init
changed: subclasses OSFS

0.2c
added: generateShareId(hostname, sharename)
changed: shareId is now 'share.host' subdomain style
         to be able to map to a file name.
fixed: now calls super class init
fixed: missing import SubFS
fixed: now passthru all fs methods
"""

def generateShareId(hostname, sharename):
    return sharename +'.'+ hostname

class BlackstrapFS(OSFS):
    
    
    ###### class methods ######

    # class method
    def initHost(hostname=None):
        """
        0.1
        The BlackstrapFS serves files from
        a virtual context. The context is
        kept inside the class.
        """
        if hostname is None:
            BlackstrapFS.__hostname = gethostname()
        else:
            BlackstrapFS.__hostname = hostname
        BlackstrapFS.__shares = dict()
        
        return BlackstrapFS
    
    
    
    # class method
    def addShare(srcaddr,
                 sharename
                ):
        """
        0.1
        Shares are added to the class itself.
        An instance of the service can
        select which share to serve.
        """
        
        #todo: check for blank hostname
        #todo: check for existing before...
        
        shares = BlackstrapFS.__shares
        
        shareid = generateShareId( 
            BlackstrapFS.__hostname, 
            sharename)
        
        shares[shareid] = srcaddr
        
        return BlackstrapFS
    
    # class method
    def closeHost():
        pass
    
    ###### Instance methods ######
    
    def __init__(self,urlstr,*args):
        # todo: require file scheme
        self._urlstr = urlstr
        
        url = urlparse(urlstr)
        self.url = url
        #shares = BlackstrapFS.__shares
        shares = BlackstrapFS.__shares
        shareid = url.netloc
        
        try:
            sharepath = shares[shareid]
            realpath = sharepath+'/'+url.path
        except:
            raise CreateFailed(shareid)
        
        super().__init__(realpath,*args)
        
        
    def geturl(self,path):
        # if path starts with '/'
        _urlstr = self._urlstr.rstrip('/')
        _path = path.lstrip('/')
        if(_path == ""):
            # if there is no path,
            # we must return _urlstr as inited.
            # It may match an entry in the fstab.
            return self._urlstr
        return f"{_urlstr}/{_path}"
        
        
    def _close(self):
        pass
    
    if six.PY2:
        def close(self):  # noqa: D102
            self._close()
            super(BlackstrapFS, self).close()
    else:
        def close(self): # noqa: D102
            self._close()
            super().close()
                    
            
    ####################
    #  cosmos API      #
    ####################
    
    # DEPRICATE THIS
    # DO NOT ADD EXTERNAL API

    def lookup(self, path, base=None):
        # FIXME: Placeholder.
        return True
    