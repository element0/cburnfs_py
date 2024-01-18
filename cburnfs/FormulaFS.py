from fs.base import FS
from fs.info import Info
from fs.enums import ResourceType
from fs.errors import DirectoryExpected
from io import BytesIO
from hashlib import sha256
import json
from DcelJSONHashEncoder import dumphash
from DcelJSONEncoder import dumpdcel

def sample_function(*args, **kwargs):
    print("FormulaFS sample function side-effect.")
    return "Sample function return value."

class FormulaFS(FS):
    """
    Serve the output of a command via FS API.
    
    Handle buffering.
    """
    def __init__(self, formula_dict):
        super().__init__()
        if(type(formula_dict) == dict):
            # set self._formula_dict before calling 
            # hash_of_formula_dict()
            self._formula_dict = formula_dict

            if 'fn' in formula_dict:
                self._formula_name = formula_dict['fn']
                self._formula_hash = self.hash_of_formula_dict()
            else:
                raise Exception("FormulaFS requires a function 'fn' in the initialization dict.")
            self._buffer = None
        else:
            raise TypeError('FormulaFS requires a dict to initialize.')
            
    def __repr__(self):
        return f"<FormulaFS({self._formula_dict})>"
    
    # ---- FS overloads ----
    
    def getinfo(self, path, namespaces=['basic']):
        nodetype = ResourceType.unknown
        return Info({
            'basic': {
                 'name': self._formula_name,
                 'is_dir': False
             },
        })
    
    def listdir(self, path):
        raise DirectoryExpected(path)
    
    def makedir(self, path, *args, **kwargs):
        raise ResourceInvalid(self._formula_name)
    
    def openbin(self, path, *args, **kwargs):
        if self.isdirty or (self._buffer == None):
            buf = self._formula_dict['fn'](*(self._formula_dict['args']))
            self.flushbuffer(buf)
        else:
            buf = self._buffer
        if not hasattr(buf, 'encode'):
            buf = dumpdcel(buf)
        return BytesIO(buf.encode())
    
    def remove(self, path, *args, **kwargs):
        raise ResourceInvalid(self._formula_name)
    
    def removedir(self, path, *args, **kwargs):
        raise ResourceInvalid(self._formula_name)
    
    def setinfo(self, path, *args, **kwargs):
        raise ResourceInvalid(self._formula_name)
    
    def hash(self, name=''):
        """Return hash of the dictionary that defines the formula."""
        if not hasattr(self, '_formula_hash'):
            _formula_hash = self.hash_of_formula_dict()
            self._formula_hash = _formula_hash
            return _formula_hash
        if self.isdirty:
            return self.hash_of_formula_dict()
        return self._formula_hash
    
    # ---- Iterator support ----
    
    def __iter__(self):
        if not hasattr(self._buffer, '__iter__'):
            return TypeError(f'Output from {self._formula_name} is not iterable.')
        # These are iterable.
        if type(self._buffer) == dict:
            # Allows conversion from dict to dict.
            return self._buffer.items().__iter__()
        return self._buffer.__iter__()
    
    # ---- String support ----
    
    def __str__(self):
        return self.readtext('')
    
    # ---- Introspection ----
    
    def __desc__(self):
        return self._formula_name
    
    # ---- Direct value access ----
    
    @property
    def value(self):
        if self._buffer == None:
            buf = self._formula_dict['fn'](*(self._formula_dict['args']))
            self.flushbuffer(buf)
        else:
            buf = self._buffer
        return buf
            
    # ---- Checksum support ----
    def hash_of_formula_dict(self):
        return dumphash(self._formula_dict)
    
    @property
    def isdirty(self):
        return self._formula_hash != self.hash_of_formula_dict()
    
    # ---- Buffer ----
    def flushbuffer(self, buf):
        self._buffer = buf
        self._formula_hash = self.hash_of_formula_dict()
    