from fs.base import FS
from fs.info import Info
from fs.enums import ResourceType
from fs.errors import DirectoryExpected
from fs.errors import ResourceInvalid
from fs.errors import ResourceReadOnly
from io import BytesIO
from sys import getsizeof

class ValueSvc(FS):
    
    def __init__(self, value):
        self.__value = value
        
    # ---- pyfilesystem API ----
        
    def getinfo(self, path, namespaces=['basic']):
        """Get info about the value.
        
        The most relevant info will be in the details namespace.
        
        If this function uses sys.getsizeof, it will return the
        memory footprint of the python object, not the length
        in bytes of the data of interest.
        """
        info = {
            'basic': {
                'name': str(type(self.__value)),
                'is_dir': False
            }
        }
        if 'details' in (namespaces if namespaces else []):
            details = {
                'size': getsizeof(self.__value)
            }
            info.update(details)
        return Info(info)
    
    def listdir(self, _):
        raise DirectoryExpected('ValueSvc value does not have a directory.')
    
    def makedir(self, _):
        raise ResourceInvalid('ValueSvc cannot make a directory inside a value.')
    
    def openbin(self, _, *args, **kwargs):
        return BytesIO(str(self.__value).encode())
    
    def remove(self, _):
        raise ResourceInvalid('ValueSvc cannot have directories inside a value. Nothing to remove.')
    
    def removedir(self, _):
        raise ResourceInvalid('ValueSvc cannot have directories inside a value. Nothing to remove.')

    def setinfo(self, _):
        raise ResourceReadOnly('ValueSvc cannot set arbitrary info.')
    
    def isdir(self, _):
        """ValueSvc::isdir() unconditionally returns false."""
        return False
    
    def writetext(self, _, value):
        self.__value = value
    
    # ---- Dcel API ----
    
    @property
    def value(self):
        """Returns the internal value."""
        return self.__value
    
    @value.setter
    def set_value(self, value):
        """Sets the internal value."""
        self.__value = value
    