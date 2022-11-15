from fs.base import FS
from fs.info import Info
import six
from fs.errors import ResourceNotFound, DirectoryExpected
from copy import deepcopy
from MulticelFS import MulticelFS

def mergehostinfo(A,B,out=None):
    pass

def mergeinfo(A,B,out=None):
    # type: (dict, dict, dict) -> dict()

    if out is None:
        _out = dict()
    else:
        _out = out
    
    if A == dict():
        return deepcopy(B)
    
    for k,v in A.items():
        if k in B:
            vB = B[k]
            if type(v) is dict and type(vB) is dict:
                _out[k] = dict()
                mergeinfo(v,vB,_out[k])
            elif type(v) is list and type(vB) is list:
                #quick fix
                #todo: upgrade w mergehostinfo()
                _out[k] = list(set(v)|set(vB))
            else:
                _out[k] = B[k]
        else:
            _out[k] = A[k]
    for k,v in B.items():
        if not k in _out:
            _out[k] = B[k]
    return _out

class MulticelSeqFS(MulticelFS):
    def __init__(self, dcels):
        super().__init__(dcels)
    
    def listdir(self,path): # Get a list of resources in a directory.
        lsprep = list()
        for ea in self.dcels:
            try:
                lsprep.extend(
                    ea.listdir(path)
                )
            except ResourceNotFound:
                pass
            except DirectoryExpected:
                pass
        return lsprep

    
    # non-FS API specific to MultiCelFS
    #def add_dcel(self, dcel):
    #def remove_dcel(self, dcel):
    # def get_dcel_by_host(self,hostname):
