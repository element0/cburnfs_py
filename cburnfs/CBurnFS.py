from fs.osfs import OSFS
from fs.base import FS
from fs.info import Info
from fs.errors import ResourceNotFound
from fs.copy import copy_dir, copy_file

from MulticelFS import MulticelFS
from blackstrap import BlackstrapFS
from Dcel import Dcel # factor out
from APath import APath
from Fudge import Fudge
from copy import deepcopy
import json
import six
from urllib.parse import urlparse
from os.path import split
if six.PY2:
    from urllib import unquote
else:
    from urllib.parse import unquote

#for merge lib (tbd): mergeinfo


_version='0.15'

# 0.15

# Trimming the fat. 

# 0.14

# added hiena_mp() parser to APath cosm
#   to parse fstab.

# 0.13

# refactored Dcel, APath, MulticelFS
# wip: change usage: CBurnFS(path)

# works: getinfo(), readtext(), readbytes()
# fixme: getinfo iterates over code block twice. why?

# 0.12b
# wip: propertyupdate() removeHost()
# fixed: updateHosts() makedir() now ignores existing dirs
# fixed: updateHosts() unquote %20 in path
# fixed: removeHosts() unquote %20 in path

# 0.11c
# wip: propertyupdate()
# removed Dcel.getinfo() debug output
# add CBurnFS.updateHosts()
# fixme: MulticelFS close constituents if needed
# fixed typo
# fixing propertyupdate updatehosts()

# 0.10a
# fixed missing json import
# works with BlackstrapSvc
# solely uses `cosm` dict to initialize

# 0.9
# added: CBurnFS subclasses FS
# added: readbytes() via FS subclass
# fixed: mergeinfo() mutable default argument caused getinfo() to report on different path
        
# usage:
# cbfs = CBurnFS(bootpath)

def init_dcel_from_url(boot,url):
    dc = None
    return dc

FSTAB_RELPATH = '@/etc/fstab'
FSTAB_ABSPATH = '/@/etc/fstab'

class CBurnFS(APath):        
    
    def __loadFstab(self, bootpath: str):
        boot = Fudge(bootpath)
        # FIXME: must force load of root - consider this a bug
        boot_root = boot/'/'
        fstab = boot/FSTAB_RELPATH
        cels = []
        for ea in fstab:
            if ea/'vfstype' == 'cburnfs':
                urlstr = ea/'spec'
                _scheme = ea/'spec.url/scheme'
                if _scheme == '':
                    _scheme = 'file'
                service_class = boot._apath.cosm['services'][str(_scheme)].value
                try:
                    cels += [ Dcel(address=str(urlstr), 
                                service_class=service_class) ]
                except:
                    pass
        root = Dcel(
            service_class=MulticelFS,
            address=cels
        )
        return root
                
    def __init__(self, bootpath: str):
        self._bootpath = bootpath
        root = self.__loadFstab(bootpath)
        super().__init__(root)
        
    def _reinit(self):
        print(f"CBurnFS::_reinit() called.")
        root = self.__loadFstab(self._bootpath)
        super()._reinit(root)
        
        
    # updater junk
    def updateHosts(self,path,hosts):
        
        dcel = self.target
        svc = dcel.service
        
        _path = unquote(path)
        pathDir,pathBase = split(_path)
        
        if type(svc) == MulticelFS:   
            for host in hosts:
                
                # get host fs
                dest = svc.get_dcel_by_host(host)
            
                # make path on host fs
                destSvc = dest.service
                destDirFS = destSvc.makedirs(pathDir,None,True)
                
                # copy path from multifs
                #   to path in host fs
                
                if svc.getinfo(_path).is_dir:
                    copy_dir(svc,_path,destDirFS,pathBase)
                else:
                    copy_file(svc,_path,destDirFS,pathBase)            
            

    def removeHosts(self,path,hosts):
        
        _path = unquote(path)
        pathDir,pathBase = split(_path)
        dcel = self.target
        svc = dcel.service
        
        if type(svc) == MulticelFS:   
            for host in hosts:
                # get host fs
                dest = svc.get_dcel_by_host(host)
        
                if dest.getinfo(_path).is_dir:
                    dest.service.removetree(_path)
                else:
                    dest.service.remove(_path)
                    
    def urlListFromDict(self, path, ob) -> list:
        dirlist = list()
        if type(ob) is dict:
            for each in ob:
                dirlist = dirlist + self.urlListFromDict(f"{path}/{each}", ob[each])
        else:
            return [(path, ob)]
        return dirlist

    def updateMultiValue(self, path, multiValue):
        """multiValue should already have been parsed."""
        _path = unquote(path)
        target = self.target
        svc = target.service
        actionPairs = self.urlListFromDict(_path, multiValue)
        root_fu = Fudge(self)
        for url,val in actionPairs:
            (root_fu/url)['.'] = val
    
    # webdav style updaters
    
    def propertyupdate(self,path,uprq):
        
        print(f"CBurnFS::propertyupdate(): path={path}, uprq={uprq}")
        
        for verb in uprq:
            if verb == 'append':
                if "cburn" in uprq[verb]:
                    target = uprq[verb]["cburn"]
                    if "hosts" in target:
                        self.updateHosts(
                            path,
                            target["hosts"])
                    if "multivalue" in target:
                        self.updateMultiValue(
                            path,
                            target["multivalue"])
                        if(path.startswith(FSTAB_RELPATH)
                           or path.startswith(FSTAB_ABSPATH)):
                            self._reinit()
            
            if verb == 'remove':
                if "cburn" in uprq[verb]:
                    target = uprq[verb]["cburn"]
                    if "hosts" in target:
                        self.removeHosts(path,
                            target["hosts"])
                
        return 'CBurnFS.propertyupdate():return: improve this response'
    
    def processRequest(self,path,rq):
        # rq is a dict object from flask app.
        print(f"CBurnFS::processRequest() rq={rq}")
        response = dict()
        for mod in rq:
            if mod == 'propertyupdate':
                response[mod] = self.propertyupdate(path,rq[mod])
        return response
    