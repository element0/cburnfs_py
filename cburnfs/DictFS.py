from fs.base import FS
from fs.subfs import SubFS
from fs.info import Info
from os.path import basename, dirname
from fs.errors import ResourceNotFound, ResourceReadOnly
from fs.errors import RemoveRootError
from fs.errors import DirectoryExists, DirectoryNotEmpty
from fs.errors import FileExpected, DirectoryExpected
from io import BytesIO
from Dcel import Dcel

DirectoryTypes = (dict,list,Dcel)
ByteableTypes = (bytes,str)
FlexibleTypes = (Dcel,)
WriteModes = ('w','a')

class DictFS(FS):
    def __init__(self,fsdict,mode='a'):
        if(type(fsdict) is str):
            fsdict = { fsdict: fsdict }
        self.fsdict = fsdict
        self._mode = mode
        super().__init__()
    
    @property
    def _addr(self):
        return self.fsdict
    
    def _pathwalk(self,
                  path,
                  target=None
                 ):
        if target is None:
            target = self.fsdict
            
        if (not type(target) is dict):
            # UPDATE 8/7/2022 - raygan - Return fsdict without lookup.
            # This enables Fudge glob where fu/'*' needs to return a list.
            if (type(target) is Dcel
                or str(type(target)) == "<class '__main__.Dcel'>"):
                return target._pathwalk(path)
            else:
                raise TypeError(f"DictFS internal 'fsdict' type must 'dict' or 'Dcel' not {type(target)}.")
        
        if path in (None,"",".","/"):
            return target
        
        path = path.strip("/")

        split_result = path.split('/',1)
        if len(split_result) == 2:
            seg,nextpath = split_result
        else:
            seg = split_result[0]
            nextpath = None

        # lookup seg within target.
        # target may be a Dict or Dcel
        if not seg in target:
            raise ResourceNotFound(path)

        nexttarget = target[seg]

        if ((type(nexttarget) is dict
            or type(nexttarget) is Dcel)
            and not nextpath is None):
            return self._pathwalk(nextpath,
                                  nexttarget)
        return nexttarget
    
    
    ####################
    # pyfilesystem Api #
    ####################
    
    def getinfo(self, path, namespaces=None):
        is_dir = self.isdir(path)
            
        i = Info({"basic":{
            "name": basename(path.strip('/')),
            "is_dir": is_dir
        }})
        
        if namespaces != None \
        and "dcel" in namespaces:
            target = self._pathwalk(path)
            i.raw["dcel"] = {"value":
                             target
                            }
        return i
    
    def listdir(self, path):
        if self.isdir(path):
            target = self._pathwalk(path)
            if type(target) != type(None):
                try:
                    # This might fail if Dcel::iter() doesn't work.
                    res = list(target)
                except:
                    res = None
                if type(res) == type(None):
                    return []
                return list(target)
            else:
                return []
        raise DirectoryExpected(path)
    
    def isdir(self, path='/'):
        target = self._pathwalk(path)
        _type = type(target)
        
        if _type in DirectoryTypes:
            return True
        if _type in FlexibleTypes:
            return target.isdir(path)
            # short circuited
            _value = target.value
            if (hasattr(_value,'__getitem__')
               and not issubclass(_type,str)):
                return True
        else:
            return False
    
    def makedir(self, path, permissions=None, recreate=False):
        
        if not self._mode in WriteModes:
            # raise ReadOnlyFilesystem
            return
        
        parpath = dirname(path)
        entryname = basename(path)
        target = self._pathwalk(parpath)
        if target is None:
            raise ResourceNotFound
            
        if entryname in target\
        and recreate is False:
            raise DirectoryExists(path)
        
        target[entryname] = dict()
        
        return SubFS(self, path)
    
    def openbin(self, path, mode='r', buffering=-1, **options):
        
        if mode in WriteModes\
        and not self._mode in WriteModes:
            raise ResourceReadOnly(f"DictFS: {path}")
        parpath = dirname(path)
        entryname = basename(path)
        parent = self._pathwalk(parpath)
        target = parent[entryname]
        targettype = type(target)
        
        if targettype in DirectoryTypes:
            raise FileExpected(path)
        
        if targettype is str:
            buf = target.encode(encoding='utf-8')
            # kludge to get writebytes to work
            # but it messes up getting strings from DictFS
            # parent[entryname] = buf
        elif targettype is bytes:
            buf = target
            
        else:
            raise FileExpected(path)
        
        return BytesIO(buf)
    
    def remove(self, path):
        if not self._mode in WriteModes:
            # raise ReadOnlyFilesystem
            return
        
        parpath = dirname(path)
        entryname = basename(path)
        pardir = self._pathwalk(parpath)
        if entryname in pardir:
            if not type(pardir[entryname]) in DirectoryTypes:
                pardir.pop(entryname)
            else:
                raise FileExpected(path)
        else:
            raise ResourceNotFound(path)
        
    def removedir(self, path):
        if not self._mode in WriteModes:
            # raise ReadOnlyFilesystem
            return
        
        if path == "/":
            raise RemoveRootError
            
        parpath = dirname(path)
        entryname = basename(path)
        pardir = self._pathwalk(parpath)
        if entryname in pardir:
            if type(pardir[entryname]) in DirectoryTypes:
                if pardir[entryname]:
                    raise DirectoryNotEmpty(path)
                else:
                    pardir.pop(entryname)
            else:
                raise DirectoryExpected(path)
        else:
            raise ResourceNotFound(path)
        
        
    def setinfo(self, path, info):
        if not self._mode in WriteModes:
            # raise ReadOnlyFilesystem
            return
        try:
            parpath = dirname(path)
            entryname = basename(path)
            target = self._pathwalk(parpath)
        except:
            return
        try:
            value = info['dcel']['value']
            target[entryname] = value
        except:
            return
        
    ### pyfilesystem:
    #   override methods
    
    def writetext(self,
                  path,
                  contents,
                  encoding='utf-8',
                  errors=None,
                  newline=''):
        if not self._mode in WriteModes:
            raise ResourceReadOnly
        try:
            # walk to target
            parpath = dirname(path)
            entryname = basename(path)
            target = self._pathwalk(parpath)
        except:
            return
        try:
            # set target
            result = target[entryname]
            if type(result) is Dcel:
                result.value = contents
            else:
                target[entryname] = contents
        except:
            return
    
    ####################
    #  cosmos API      #
    ####################
    
    # Depricate external use of any API other than pyfilesystem.
    # OK to keep if this is internal.

    def lookup(self, path, base=None):
        return self._pathwalk(path, base)
        