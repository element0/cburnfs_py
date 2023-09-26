from fs.osfs import OSFS
from fs.base import FS
from fs.info import Info
from fs.errors import ResourceNotFound
from fs.copy import copy_dir, copy_file
from fs.walk import Walker

from MulticelFS import MulticelFS
from Dcel import Dcel # TODO: factor out
from APath import APath
from Fudge import Fudge
from metafs import MetaFS
from metafs_proxy import MetaFSProxy
from mergeinfo import mergeinfo

from copy import deepcopy
import json
import six
from urllib.parse import urlparse
from os.path import split
if six.PY2:
    from urllib import unquote
else:
    from urllib.parse import unquote
from threading import Thread
import logging


def setup_logger():
    default_logging = logging.getLogger('CBurnFS-py')
    default_logging.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    default_logging.addHandler(ch)
    
setup_logger()
default_logging = logging.getLogger('CBurnFS-py')

#for merge lib (tbd): mergeinfo


_version='0.19'

# Adding MetaFSProxy to store custom metadata.

# --- version 0.16 goals INHERIT
# Refactoring to simplify dependencies.
# Goal is an independent, installable python module.

# usage:
# cbfs = CBurnFS(bootpath)

def init_dcel_from_url(boot,url):
    dc = None
    return dc

FSTAB_RELPATH = '@/etc/fstab'
FSTAB_ABSPATH = '/@/etc/fstab'

# Configure the MEGA-KLUDGE!
# NOTE: the algorithm removes leading '/' from the input to be matched.
SPECIAL_PATH_HOST_SHORTID_MAP = '@/etc/fstab/?vfstype=cburn/.{@(spec):@(mntopts.cskvp[shortid])}' 

def metafs_set_progress(metafs, path, functionName, host, status):
    info = metafs.getinfo(path).raw
    info.update({"progress":{host:{functionName:status}}})
    metafs.setinfo(path,info)
    
def metafs_remove_progress(metafs, path, functionName, host):
    info = metafs.getinfo(path).raw
    del(info['progress'][host][functionName])
    if len(info['progress'][host]) == 0:
        del(info['progress'][host])
    if len(info['progress']) == 0:
        del(info['progress'])
    metafs.setinfo(path,info)

def copy_executor(metafs, path, host, copy_func, fs1, path1, fs2, path2):
    metafs_set_progress(metafs, path, "updateHosts", host, "pending")
    copy_func(fs1, path1, fs2, path2)
    metafs_remove_progress(metafs, path, "updateHosts", host)
    
    
def remover_executor(metafs, path, host, remover_func, func_self, target_path):
    metafs_set_progress(metafs, path, "removeHosts", host, "pending")
    remover_func(target_path)
    metafs_remove_progress(metafs, path, "removeHosts", host)


class CBurnFS(APath):
    
    def __loadFstab(self, bootpath: str):
        boot = Fudge(bootpath)
        # FIXME: must force load of root - consider this a bug
        boot_root = boot/'/'
        fstab = boot/FSTAB_RELPATH
        cels = []
        metafs_conf = dict()
        host_shortname_map = dict()
        for ea in fstab:
            """
            The fstab parser is located in the APath Cosm.
            It might not handle tabs. Try to use spaces only.
            """
            if ea/'vfstype' == 'cburnfs':
                urlstr = ea/'spec'
                _scheme = ea/'spec.url/scheme'
                if _scheme == '':
                    _scheme = 'file'
                service_class = boot._apath.cosm['services'][str(_scheme)].value
                try:
                    cels += [ Dcel(address=str(urlstr), service_class=service_class) ]
                except:
                    pass
                try:
                    host_shortname_map[ea/'spec'] = ea/'mntopts/shortid'
                except:
                    pass 
            if ea/'vfstype' == 'cburnfs-meta':
                '''
                The last 'cburn-metafs' defined will succeed.
                '''
                host_and_port = str(ea/'spec.url/netloc').split(':')
                metafs_conf['REDIS_CONTAINER_NAME'] = host_and_port[0]
                if len(host_and_port) > 1:
                    metafs_conf['REDIS_CONTAINER_PORT'] = int(host_and_port[1])
                else:
                    metafs_conf['REDIS_CONTAINER_PORT'] = 6379
                try:
                    metafs_conf['USERPUBLICID'] = str(ea/'mntopts.cskvp/userid')
                except:
                    metafs_conf['USERPUBLICID'] = 'unset'
                try:
                    metafs_conf['USERHOMENAME'] = str(ea/'mntopts.cskvp/userhome')
                except:
                    metafs_conf['USERHOMENAME'] = 'unset'
                try:
                    metafs_conf['USERFSURL'] = str(ea/'mntopts.cskvp/userurl')
                except:
                    metafs_conf['UESRFSURL'] = 'unset'
                
        root = Dcel(
            service_class=MulticelFS,
            address=cels
        )
        meta = MetaFS(config=metafs_conf)
        self.host_shortname_map = host_shortname_map
        return root, meta
              
    def __new__(cls,
             addr=None,
             servicename=None,
             parent=None,
             logging=default_logging
            ):
        return super().__new__(cls)
    
    def __init__(self,
             addr=None,
             servicename=None,
             parent=None,
             logging=default_logging
            ):
        self.logging = logging
        self._bootpath = addr
        root, meta = self.__loadFstab(addr)
        self.metafs = meta
        metaproxy = MetaFSProxy(root,meta)
        super().__init__(Dcel(service=metaproxy))
        self._init_listener_system()
        
    def _reinit(self):
        print(f"CBurnFS::_reinit() called.")
        root, meta = self.__loadFstab(self._bootpath)
        super()._reinit(root)
        
        
    # updater magic
        
    def updateHosts(self,path,hosts):
        
        metaproxy = self.target.service
        metafs = metaproxy.metafs
        dcel = metaproxy.targetfs   # note: unsyncs metafs until next getinfo()
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
                    copy_func = copy_dir
                else:
                    copy_func = copy_file
                    
                # WIP This assumes that svc and destDirFS
                # are thread-safe.
                copy_thread = Thread(target=copy_executor,
                    args=[metafs,path,host,
                          copy_func,svc,_path,destDirFS,pathBase]
                )
                copy_thread.start()

    def removeHosts(self,path,hosts):
        
        metaproxy = self.target.service
        metafs = metaproxy.metafs
        dcel = metaproxy.targetfs   # note: unsyncs metafs until next getinfo()
        svc = dcel.service
        
        _path = unquote(path)
        pathDir,pathBase = split(_path)
        
        if type(svc) == MulticelFS:   
            for host in hosts:
                # get host fs
                dest = svc.get_dcel_by_host(host)
        
                if dest.getinfo(_path).is_dir:
                    remover_func = dest.service.removetree
                else:
                    remover_func = dest.service.remove
                    
                # WIP This assumes that dest.service
                # is thread-safe.
                remover_thread = Thread(target=remover_executor,
                    args=[metafs,path,host,
                          remover_func,dest.service,_path]
                )
                remover_thread.start()
                    
                    
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
    
    # ---- listener notification system ----
    
    def _init_listener_system(self):
        self._flow = {'listen':dict()}
        
    def add_listener(self,tag,listener):
        tags = self._flow['listen']
        if not tag in tags:
            tags[tag] = []
        tags[tag].append = listener
        
    def remove_listener(self,tag,listener):
        tags = self._flow['listen']
        if not tag in tags:
            return
        if listener in tags[tag]:
            tags[tag].remove(listener)
            
    # ---- Metadata Methods ----
    
    def disk_usage(self, path='/'):
        '''
        Estimate disk usage in bytes.
        
        WARNING: Skip 'permission' denied and other errors.
        
        This might not be a bad thing. If the user doesn't have permission,
        they probably don't have business managing those files.
        
        Other errors? Maybe need to handle them.
        '''
        if self.isdir(path):
            subdir = self.opendir(path)
            w = Walker.bind(subdir)
            return sum([ info.size
                        for _,info in w.info(namespaces=['details'],
                                             ignore_errors=True
                                            ) ])
        else:
            return self.getsize(path)
            
    # ---- FS shadow methods ----
    def getinfo(self, path='/', namespaces=['basic']):
        if namespaces == None:
            return super().getinfo(path)
        if 'cburnfs' in namespaces:
            cburnfs_info = {
                'cburnfs': {
                    'size': self.disk_usage(path)
                }
            }
            other_info = super().getinfo(path, namespaces).raw
            merged_info = mergeinfo(cburnfs_info, other_info)
            return Info(merged_info)
        return super().getinfo(path, namespaces)
        
    def readbytes(self, path=None):
        self.logging.debug(f'readbytes({path})')
        # MEGA-KLUDGE!
        # NOTE: the algorithm removes leading '/' from the input to be matched.
        if path.lstrip('/') == SPECIAL_PATH_HOST_SHORTID_MAP:
            self.logging.debug(f'CBurnFS: readbytes: cleaned path: {path.lstrip("/")}')
            boot = Fudge(self)
            self.logging.debug('CBurnFS: Fudge booted')
            # FIXME: must force load of root - consider this a bug
            boot_root = boot/'/'
            self.logging.debug('CBurnFS: locating fstab')
            fstab = boot/FSTAB_RELPATH
            self.logging.debug('CBurnFS: building `host_shortid_map`')
            host_shortid_map = {
                str(ea/'spec'): str(ea/'mntopts.cskvp/shortid')
                for ea in fstab
                if ea/'vfstype' == 'cburnfs'
            }
            self.logging.debug('CBurnFS: built `host_shortid_map`')
            return bytes(json.dumps(host_shortid_map), encoding='utf-8')
        else:
            return super().readbytes(path)
    
    def writetext(self, path=None, contents='', encoding='utf-8',
                  errors=None, newline=''):
        # dirty hook to avoid fleshing out listener system
        if path == FSTAB_ABSPATH:
            old_content = self.readtext(path)
            if not old_content == contents:
                super().writetext(path,contents,encoding,errors,newline)
                self._reinit()
        else:
            super().writetext(path,contents,encoding,errors,newline)

            