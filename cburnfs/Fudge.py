from APath import APath, APathWrapper
from os.path import basename
from urllib.parse import urlparse


from DictFS import DictFS
from MulticelSeqFS import MulticelSeqFS
from Dcel import Dcel

def fudgeglob(apath,expr):
    dcel_list = list()
    res_dcel = Dcel(dcel_list,
                    service_class=MulticelSeqFS
                   )
    res = Fudge(apath.spawn(expr,
                            res_dcel))
    return res


class Fudge(APathWrapper):
    
    def __init__(self,source):
        # default string to 'file'
        srctype = type(source)
        if srctype is str:
            service_class = 'file'
            apath = APath(source, 
                          service_class
                         )
        if issubclass(srctype,APath):
            apath = source
        if issubclass(srctype,(dict, list)):
            service_class = 'dict'
            apath = APath(source, 
                          service_class
                         )
        # APathWrapper initializes
        #   self._apath
        super().__init__(apath)
        
    def _getdir(self):
        if self._apath.isdir():
            return self
        else:
            try:
                addr = self._apath.target.address
                typename = basename(addr)
                res = self.__getattr__(typename)
                if res._apath.isdir():
                    return res
            except:
                raise
        raise NotADirectoryError
    
    def __getitem__(self, item: str):
        """
        Return child from directory
        surface of the domain,
        wrapped in fudge.
        
        If the parent is a glob,
        then the item returned is a
        list of matching items for
        each item in the glob result.
        
        If the item is a glob, then
        spawn a new target with fudge
        """
        
        if item == '.':
            return self
        
        if hasattr(self._apath,'_isglob'):
            res = Fudge([ea[item]
                          for ea in self
                         ])
            res._apath._isglob = True
            return res
        
        if item == '*':
            res = Fudge([ea for ea in self])
            res._apath._isglob = True
            return res
        
        directory = self._getdir()

        if item == '*':
            dcel = directory._apath.target
            items = [dcel[ea]
                     for ea in dcel.listdir()]
            globcel = Dcel(items,
                           service_class=MulticelSeqFS)
            globapath = self._apath._spawn('*',globcel)
            globapath._isglob = True
            return Fudge(globapath)
        
        return Fudge(directory._apath.getchild(item))
    
    def __setitem__(self, pathstr, value):
        target = self[pathstr]._apath.target
        target.value = value
        print(f"Fudge::__setitem__() target.value type: {type(target.value)}")
        target.value.flush()
        
    def __getattr__(self, typename):
        """
        Return a cosmos 'type'
        mutation of the _apath.
        """
        #1. lookup cosm/type
        #2. mutate the apath
        
        #typefn = self._apath.cosm['types'][typename]
        mutation = self._apath.command(dict, typename, ~(self._apath.target))
        return Fudge(mutation)
    
    def __call__(self, *args, **kwargs):
        """
        Pass domain through a function.
        """
        return Fudge(self._apath)
    
    #def __truediv__(self, item):
        #!!! this is overridden below
    
    def __matmul__(self, item):
        return self.__getattr__(item)
    
    def __mul__(self, item):
        return self.__getattr__(item)
    
    def __gt__(self, other):
        if other == 'hello':
            return 'hi'
        return Fudge(self._apath)
    
    def __eq__(self, other):
        if type(other) is str:
            return str(self) == other
        else:
            raise TypeError(other)
    
    def __str__(self):
        return str(self._apath.target)

    def __iter__(self):
        try:
            directory = self._getdir()
            if hasattr(self._apath,'_isglob'):
                return iter([ea for ea in directory._apath.listdir()])
            return iter([self[ea] for ea in directory._apath.listdir()])
        except:
            return iter([self])
        
            
# Fudge pathwalk

def splitexists(fudgeob, seg, c='.'):
    parts = seg.split(c)
    i = 0
    matchi = -1
    match = ''
    trypart = ''
    fudgeob = fudgeob._getdir()
    for part in parts:
        if trypart == '':
            trypart = part
        else:
            trypart += c + part
        if fudgeob._apath.exists(trypart):
            matchi = i
            match = trypart
        i += 1
    return (match,parts[matchi+1:])

def fudgedots(nextfudge,suffixes):
    for suf in suffixes:
        nextfudge = nextfudge.__getattr__(suf)
    return nextfudge

def fudgedot(fudgeob,path):
    if hasattr(fudgeob._apath,'_isglob'):
        array = [fudgedot(each,path)
                 for each in fudgeob]
        res = Fudge(array)
        res._apath._isglob = True
        return res
    exists,segs = splitexists(fudgeob,path,'.')
    nextfudge = fudgeob
    if exists != '':
        nextfudge = fudgeob[exists]
    if segs == []:
        return nextfudge
    else:
        return fudgedots(nextfudge, segs)

def fudgestar(fudgeob,segs):
    ar = [ fudgesegs(fudgeob[name],segs)._apath.target.value
            for name in fudgeob ] 
    return Fudge(ar)

def fudgesegs(nextfudge,segs):
    for seg in segs:
        if seg == '*':
            nextfudge = nextfudge[seg]
            continue
        nextfudge = fudgedot(nextfudge,seg)
    return nextfudge

def fudgewalk(fudgeob,path):
    try:
        return fudgeob[path]
    except KeyError:
        exists,segs = splitexists(fudgeob,path,'/')
        if segs == []:
            return fudgedot(fudgeob,path)
        if exists != '':
            nextfudge = fudgeob[exists]
            return fudgesegs(nextfudge, segs)
        else:
            return fudgesegs(fudgeob, segs)

Fudge.__truediv__ = fudgewalk