from fs.base import FS
from fs.osfs import OSFS
from fs.multifs import MultiFS
from Dcel import Dcel
from Dcel import Dcel as D
from DictFS import DictFS
from ApathRootCosm import apathRootCosm
from fs.errors import ResourceNotFound
from urllib.parse import urlparse

METADIRNAME = ".cosm"


class APathWrapper:
    """
    Inherit this class before wrapping an Apath.
    
    Subclasses can be unwapped by APath.
    """
    
    def __init__(self, apath):
        self._apath = apath
        

class APath(FS):
    
    # Any APath created without
    # a parent inherits the class
    # environment.
    _rootcosm = Dcel(address=apathRootCosm,
                  service_class=DictFS,
                  args=['r']
                 )
    _rootcosm_atdir = Dcel({'@':apathRootCosm}, service_class=DictFS)
        
    def __new__(cls,
                addr=None,
                servicename=None,
                parent=None
                ):
        """
        Check to see if we can
        unwrap an Apath from
        a subclass of APathWrapper.
        Otherwise, create a new instance.
        """
        if issubclass(addr.__class__,
                      APathWrapper):
            return addr._apath

        return super().__new__(cls)
    
    
    def __init__(self,
                 addr=None,
                 servicename=None,
                 parent=None
                ):
        
        # Constructor Conditions
        # 1. Unwrap
        # 2. Begin Access
        # 3. Spawn Branch
        
        ## Unwrap
        #
        try:
            """
            In this case, the Apath
            class might be unwrapping
            an Apath from a wrapper.
            """
            if self.__inited == True:
                return
        except AttributeError:
            # a new instance.
            pass
        
        ## Init new instance
        super().__init__()
        
        ## Inherit rootcosm environment from class
        #  set .cosm (cascading operating system)
        #  .cosm is a Dcel or PyFilesystem2 FS subclass
        # THE COSM WILL BE OVERLOADED AT THE END OF THIS METHOD
        # BUT WE NEED THIS TO PROVIDE THE SERVICES FOR INIT
        if parent is None:
            self.cosm = APath._rootcosm
        else:
            self.cosm = parent.cosm
        
        ## Init directory 
        self.branch = dict()
        
        ## Set inited flag
        self.__inited = True
        
        ## Beginning Access
        #  addr is a url
        #  service is None
        if type(addr) is str and servicename is None:
            url = urlparse(addr)
            servicename = url.scheme
        
        #  addr
        #  service
        if type(servicename) is str:
            service = self.cosm['services'][servicename].value
            self.target = Dcel(address=addr, 
                               service_class=service)   
        
        ## Spawning a Branch
        #  Dcel
        #  Parent Apath
        elif type(addr) is Dcel:
            # WIP lookup instruction
            self.target = addr
            
            ## inherit from parent
            if parent is None:
                # create a readonly cel for
                # root cosm
                pass
            # else
            # cascade the parent .cosm
            # TODO
            
        # parent
        self.parent = parent
        

            
        ## Inherit rootcosm environment from class
        #  set .cosm (cascading operating system)
        #  .cosm is a Dcel or PyFilesystem2 FS subclass
        
        # - read '@' and '.@' entries
        # - cascade '@' and '.@' onto .cosm
        # Quick Hack:
        # - Make a fs.multifs::MultiFS of:
        #        parent.target Dcel, write=False
        #        this.target Dcel, write=True
        # - Make a fs.subfs::SubFS via opendir() of:
        #        theAboveResult.opendir('@')
        # - The resulting SubFS instance will allow writes
        #   only if '@' exists in the writable layer
        #   AND WHEN the @ comes into existence writes become available.

        overlay = MultiFS()
        overlay.add_fs('root',APath._rootcosm_atdir)
        if parent is not None:
            overlay.add_fs('parent',parent.target)
        overlay.add_fs('local',self.target,write=True)

        # TODO: <---- add a virtual directory with stubs for '@' and '.@'
        #      to make the following hack work in absense of those in true fs.
        stubhack = Dcel({'@':dict(),'.@':dict()},service_class=DictFS)
        overlay.add_fs('stubhack',stubhack)

        # allow @ and .@ variants
        cosm = overlay.opendir('@')
        dotcosm = overlay.opendir('.@')
        # give precedence to the @ variant
        self.cosm = MultiFS()
        self.cosm.add_fs('dotcosm',dotcosm,write=True)
        self.cosm.add_fs('cosm',cosm,write=True)

    def _reinit(self,
                 addr=None,
                 servicename=None,
                 parent=None
                ):
        self.branch = dict()
        self.__inited = True
        
        ## Beginning Access
        #  addr is a url
        #  service is None
        if type(addr) is str and servicename is None:
            url = urlparse(addr)
            servicename = url.scheme
        
        #  addr
        #  service
        if type(servicename) is str:
            service = self.cosm['services'][servicename].value
            self.target = Dcel(address=addr, 
                               service_class=service)   
        
        ## Spawning a Branch
        #  Dcel
        #  Parent Apath
        elif type(addr) is Dcel:
            # WIP lookup instruction
            self.target = addr
            
            ## inherit from parent
            if parent is None:
                # create a readonly cel for
                # root cosm
                pass
            # else
            # cascade the parent .cosm
            # TODO
            
        # parent
        self.parent = parent
        
        # overlay local environment .cosm
        # TODO
    
    def _inherit_cosm(self):
        
        # get cosm dcel from parent
        par_cosmcel = self.parent.cosm
        
        # get cosm dcel from target
        lookupfn = self.parent.cosm['sbin']['lookup']
        targ_cosmcel = self.target['.cosm']
        
        # create new dcel from both
        d = Dcel(address=[par_cosmcel, targ_cosmcel],
              service_class=CascadeCelFS)
    
    def _spawn(parent, name, dcel):
        # works as classy or self method
        ap = APath(dcel, parent=parent)
        parent.branch[name] = ap
        return ap
    
    def close(self):
        # need to close _cosm.fs[*]?
        # close DCel?
        pass
    
    def detect_service(self,addr):
        if addr is dict:
            return self.cosm['services']['dict'].value
        return self.cosm['services']['file']
    
    def start_service(self,addr,service=None):
        if service is None:
            _Service = self.detect_service(addr)
        else:
            _Service = service
        return _Service(addr)
    
    
    # lookup interface --------------
    
    def _pathwalk(self,path=""):
        if path in (None,"",".","/"):
            return self
        path = path.strip("/")
        try:
            seg,nextpath = path.split('/',1)
        except:
            return self.lookup(path)
        try:
            return self.lookup(seg)._pathwalk(nextpath)
        except:
            raise ResourceNotFound(path)
    
    def path_lookup(self,path):
        return self._pathwalk(path)
        
    def lookup(self, addr):
        """ 
        Return an entry of the current
        target's directory
        wrapped in an Apath.
        """
        try:
            d = self.target[addr]
            try:
                a = self.branch[addr]
                if a.target != d:
                    a = APath(d,parent=self)
                    self.branch[addr] = a
                return a
            except:
                a = APath(d,parent=self)
                self.branch[addr] = a
                return a
        except:
            try:
                a = self.branch[addr]
                return a
            except:
                raise
            raise
    
    def getchild(self, key):
        return self.lookup(key)
    
    def exists(self, key):
        try:
            self.lookup(key)
            return True
        except:
            return False
    
    def getprop(self, key):
        # test version only returns self
        return self
    
    # execution interface -----------
    
    def canonical_cmdline(cmdname, *args, **kwargs):
        # fixme: include args and kwargs
        return cmdname
    
    def load_function(self, fncel:Dcel):
        return fncel.value
    
    def resolve_cmdpath(self, cmdname):
        for p in self.cosm['env']['PATH'].value:
            # lookup command dcel
            _p = p.removeprefix('.cosm/')
            pathname = _p+'/'+cmdname
            cmdcel = self.cosm.path_lookup(pathname)
            if not cmdcel is None:
                break
        return cmdcel
    
    def resolve_interpreter(self, cmdcel):
        val = cmdcel.value
        if type(val) is dict:
            try:
                interp_path = val['#!'][0]
            except:
                return (None,[])
            try:
                interp_args = val['#!'][1:]
            except:
                interp_args = []
            interp_cel = self.resolve_cmdpath(interp_path)
            return (interp_cel,interp_args)
        return (None,[])

    def command(self, rtntype, cmdname, *args, **kwargs):        
        # use cache
        cmd_id = self.canonical_cmdline(cmdname, *args, **kwargs)
        #try:
          #  return self.branch[cmd_id]      
        #except:
            #pass
        if str(type(cmdname))=="<class 'function'>":
            fn = cmdname
        else:
            cmdcel = self.resolve_cmdpath(cmdname)
            interp_cel,interp_args = self.resolve_interpreter(cmdcel)
            # get function pointer
            if interp_cel != None:
                fn = self.load_function(interp_cel)
                args = interp_args + [cmdcel] + [*args]
            else:
                fn = self.load_function(cmdcel)

        # set service for return type
        if issubclass(rtntype,FS):
            service_cls = rtntype
        else:
            service_cls = self.detect_service(rtntype)
        
        # create dcel with formula
        dc = Dcel( formula=fn,
                   args=args,
                   kwargs=kwargs,
                 )
        # create service wrapper
        _dc = Dcel(address=dc, 
                   service_class=service_cls)

        # wrap in APath
        res = APath(_dc, parent=self)

        # stash
        self.branch[cmd_id] = res
        
        return res
    
    # pyfilesystem 'FS' interface ---
    
    def getinfo(self, addr=None, namespaces=None):
        return self.target.getinfo(addr,namespaces)
    
    def listdir(self,path=None):
        return self.target.listdir(path)
    
    def isdir(self,path=None):
        return self.target.isdir(path)
    
    def makedir(self,path,permissions=None,recreate=False):
        return self.target.makedir(path,permissions,recreate)
    
    def openbin(self,
            path=None,
            mode='r',
            buffering=-1):
        # Open a binary file.
        return self.target.openbin(
            path,
            mode,
            buffering)
    
    def readbytes(self, path=None):
        return self.target.readbytes(path)
        
    def readtext(self, path=None):
        return self.target.readtext(path)
        
    def remove(self,path): # Remove a file.
        return self.target.remove(path)
    
    def removedir(self,path): # Remove a directory.
        return self.target.removedir(path)
        
    def setinfo(self,path,info):  # Set resource information.
        return self.target.setinfo(path, info)
