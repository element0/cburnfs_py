from fs.base import FS
from fs.info import Info
from fs.errors import NoURL
from fs.path import normpath
from inspect import isclass, isfunction, ismethod
from urllib.parse import urlparse
from mergeinfo import mergeinfo

DEFAULT_HOST = 'localhost'

class DcelReference:
    def __init__(self,dcel):
        self._dcel = dcel
        
    def __invert__(self):
        return self._dcel
    
    def __str__(self):
        return str(self._dcel)

class Dcel(FS):
    
    def __new__(cls, arg1=None, *args, **kwargs):
        if type(arg1) is Dcel:
            return arg1
        else:
            return super().__new__(cls)
                
    
    def __init__(self,
                 address = None,
                 service = None,
                 formula = None,
                 args = None,
                 value = None,
                 service_class = None,
                 service_args = None,
                 kwargs = None,
                ):
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
        
        super().__init__()
        self.__inited = True
        
        # If the address is a dcel,
        # use the dcel's value
        # and save the dcel in case
        # it needs to be re-evaluated.
        
        # The transformation-history ivar
        # generalizes such dependencies.
        
        if type(address) is Dcel:
            self.transformation_history = address
            address = address.value
            
        if type(address) is slice:
            address = address
            
        if not service is None:
            self.service = service
            if address:
                self.address = address
            else:
                self.address = "/"
        elif (service_class and address):
            if (isclass(service_class)
                or isfunction(service_class)
                or ismethod(service_class)):
                self.address = "/"
                try:
                    url = urlparse(address)
                    hostname = url.netloc
                    path = url.path
                    if hostname == '':
                        hostname = path
                except:
                    hostname = DEFAULT_HOST
                if service_args:
                    self.service = service_class(address,**service_args)
                else:
                    self.service = service_class(address)
                self.service.__rooturl = address
                
        if formula and args:
            self.formula = formula
            self.args    = args
            self.kwargs  = kwargs
        elif formula:
            self.formula = formula
        if not value is None:
            self._value = value
        
        # address sets value
        if (address
           and service is None
           and formula is None
           and value is None
           and service_class is None):
            self._value = address
        
        # internal stubs
        self._map = None
        self._dir = None
        
    def __invert__(self):
        return DcelReference(self)
            
    def __str__(self):
        # this needs to
        # return a str version of
        # self.value
        return str(self.value)
    
    def freshen(self, a):
        if type(a) is Dcel:
            return a.value
        if type(a) is DcelReference:
            return ~a
        return a
    
    def preslice_value(self):
        _value = ""
        # value from slice
        if (hasattr(self,'address')
            and hasattr(self,'service')
            and type(self.address) is slice
            and type(self.service) is Dcel):
            if (hasattr(self,'_dirty')
                and hasattr(self,'_value')):
                _value = self._value
            else:
                _value = str(self.service.preslice_value())[self.address]
            return _value
        else: 
            # value from readtext
            try:
                _value = self.readtext()
                self._value = _value
            except:
                try:
                    _value = self.readbytes()
                    self._value = _value
                except:
                    pass
            # value from formula
            try:
                try:
                    _args = [ self.freshen(a)
                              for a in self.args ]
                except:
                    _args = []
                try:
                    _kwargs = { k:self.freshen(v) 
                           for k,v in self.kwargs.items() }
                except:
                    _kwargs = {}
                _value = self.formula(*_args,**_kwargs)
                self.value = _value
                return _value
            except:
                pass

            # value from getinfo
            try:
                i = self.getinfo(namespaces=['dcel'])
                _value = i.raw['dcel']['value']
                self._value = _value
                return _value
            except:
                pass

            # value from buffer
            try:
                _value = self._value
                return _value
            except:
                pass
        return None
    
    @property
    def value(self):
        _value = self.preslice_value()

        # value from fragment map
        if not self._map is None:
            _base = _value
            if type(_base) is bytes:
                _base = _base.decode('utf-8')
            pos = 0
            _value = ""
            for ea in self._map:
                if pos < ea:
                    _value += str(_base[pos:ea])
                _fragcel = self._map[ea][1]
                if _fragcel is self:
                    _value += str(_value)
                _value += str(_fragcel)
                advancepos = self._map[ea][0]
                if advancepos is None:
                    return _value
                pos = advancepos
            _value += str(_base[pos:])
        return _value
    
    def conform_map(self):
        """Update map with new offsets."""
        pass
        
    @value.setter
    def value(self,new_value):
        """Set the value of the Dcel.
        
        The value can be stored in multiple ways.
        The value is buffered, but the buffer may
        either be backed by something or not backed
        by anything.
        
        If the value changes, there are multiple effects.
        If the Dcel is buffered without backing,
        the buffer changes and that's that. If there
        is a backing on the Dcel (the Dcel has either a service
        or a formula attribute) then the backing needs to be
        updated.
        
        Multiple backing scenarios exist: If the Dcel
        is backed by a URL, and the entire contents of the
        dcel are updated, then the entire contents can be
        flushed to the URL in a single write operation.
        
        If the Dcel is backed by another Dcel, it possibly
        represents a fragment of the other Dcel. The changed
        fragment needs to be inserted into the backing Dcel
        and then the backing Dcel is either flushed to its URL
        or inserted into its backing cell, and so forth until
        a root backing cell is flushed to its URL.
        
        Given that multiple fragment Dcels might be updated
        in a short succession, or batch updated, it could
        be more efficient to wait until several dirty fragments
        are ready before flushing the root backing cell to 
        its URL. A time window could be implemented to
        allow serial fragment writes. A batch-flush mechanism
        could be implemented to allow fragment update batches.
        
        The Dcel fragment map allows for the representation
        of the root backing to include updated fragments. The
        Dcel.readtext() function should step through the bytes
        of the filestream and insert changed fragments.
        
        """
        
        # set buffer
        self._value = new_value
        self._dirty = True

        # write slice "fragment"
        if (hasattr(self,"address")
            and hasattr(self,"service")
            and type(self.address) is slice
            and type(self.service) is Dcel):
            self.service.fragment_updated(self.address, self)
        
        # write to service
        try:
            self.service.writetext(self.address,
                           new_value)
            return
        except:
            pass
        
        # write to setinfo
        try:
            i = {'dcel':{'value':new_value}}
            self.setinfo(i)
            return
        except:
            pass
        
    def fragment_updated(self,frag_slice,frag_dcel):
        # TODO: Set and monitor timer to flush buffer to backing.
        if self._map is None:
            self._map = dict()
        self._map.update({frag_slice.start:(frag_slice.stop,frag_dcel)})
        if (hasattr(self,"address")
            and hasattr(self,"service")
            and type(self.address) is slice
            and type(self.service) is Dcel):
            assert(not self.service is self)
            self.service.fragment_updated(self.address,self)
                    
    def flush(self):
        if (hasattr(self,"address")
            and hasattr(self,"service")):
            address = self.address
            service = self.service
            # bubble the flush...
            if (type(address) is slice
                and type(service) is Dcel):
                service.flush()
                return
            elif (type(address) is Dcel):
                address.flush()
                return
            else:
                # I have to do this tacky shit in order to
                # put my kids to bed on time.
                # ARCHITECTURE FLAW:
                # For the future: Don't add any external methods to a
                # service derived from pyfilesystem.
                # For the band-aide kludge for DictFS dcels
                # which hold Dcel's in their leaves:
                if(hasattr(service,"lookup")):
                    target = service.lookup(address)
                    if (type(target) is Dcel):
                        if not self._map is None:
                            target.value = self.value
                        target.flush()
                        return
                    
        # FIXED 8-7-2022 - raygan
        # MulticelFS needs to flush correctly.
        # The following appears to work.

        # execute the flush
        if not self._map is None:
        # The following seems super-strange
            # however, the getter will build the value
            # based on the fragment map
            # and the setter will write to backing.
            # If there is no backing, the buck stops
            # at self._value.
            self.value = self.value
        self._dirty = False
        self._map = None
            
    # Lookup interface
    def __getitem__(self,key):
        """
        Access a child of the Dcel's
        domain.
        
        Access a slice of the Dcel's
        domain.
        
        Return object with a dcel
        interface that represents a
        child from the "directory"
        surface of this dcel.
        
        The service lookup()
        method is expected to return
        an address-object suitable
        for use with the same service
        instance.
        """
        # slice
        if type(key) is slice:
            return Dcel(address=key,service=self)
        # before adding a _dir,
        # does the service see this
        # base address (not the key) as a dir?

        # testing base address for dir
        if not self.service.isdir(self.address):
            raise TypeError(self.address)

        # base address of this Dcel is a directory
        # now we can look up the key.

        if not type(self._dir) is dict:
            # self._dir is not dict
            basepath = self.address
            if basepath == '/':
                basepath = ''
            # create address ("path") of key relative to service
            path = basepath + '/' + key
            if self.service.exists(path):
                # create Dcel's internal _dir and add child
                child = Dcel(address=path,
                             service=self.service)
                self._dir = dict()
                self._dir[key] = child
                # return the child
                return child
            else:
                raise KeyError(key)
        
        try:
            # return child if already cached
            # in Dcel's internal _dir
            return self._dir[key]
        except KeyError:
            # otherwise, add child to Dcel's _dir
            # same code as further above.
            basepath = self.address
            if basepath == '/':
                basepath = ''
            path = basepath + '/' + key
            if self.service.exists(path):
                # child
                child = Dcel(address=path,
                            service=self.service)
                self._dir[key] = child
                return child
            else:
                raise KeyError(key)
        except TypeError:
            raise TypeError(self._dir)
            
    def __setitem__(self,key,value):
        self[key].value = value

    
    # Info helpers
    
    def abspath(self,path):
        if path == None:
            return self.address
        if path == '/':
            return path
        return self.address + '/' + path
    
    @property
    def hostname(self):
        try:
            return self.service.geturl('/')
        except:
            return DEFAULT_HOST
    
    def getinfo(self,
                path=None,
                namespaces=None
               ):
        path = self.abspath(path)
        info = self.service.getinfo(path,namespaces)
        # MUST allow pyfilesystem conformant subclasses
        # to omit geturl().
        rooturl = self.service.__rooturl
        if not type(rooturl) is str:
            rooturl = None
        if not rooturl is None:
            hostinfo = { 'hosts': [rooturl] }
            raw = mergeinfo(info.raw, hostinfo)
        else:
            raw = info.raw
        return Info(raw)
    
    def listdir(self,path=None):
        path = self.abspath(path)
        return self.service.listdir(path)
    
    def isdir(self,path=None):
        path = self.abspath(path)
        return self.service.isdir(path)
    
    def openbin(self,
            path=None,
            mode='r',
            buffering=-1,
            **options):
        # Open a binary file.
        path = self.abspath(path)
        return self.service.openbin(
            path,
            mode,
            buffering)
    
    def readbytes(self, path=None):
        path = self.abspath(path)
        return self.service.readbytes(path)

    def readtext(self, path=None):
        path = self.abspath(path)
        return self.service.readtext(path)
    
    def setinfo(self,path,info): # Set resource information.
        path = self.abspath(path)
        pass

    def makedir(self,*args,**kwargs):
        self.service(*args,**kwargs)
        
    def remove(self,*args,**kwargs):
        self.service(*args,**kwargs)
        
    def removedir(self,*args,**kwargs):
        self.service(*args,**kwargs)

    ### Additional Methods
    
    def _pathwalk(self,path):
        try:
            seg,nextpath = path.split('/',1)
        except:
            return self[path]
        try:
            return self[seg]._pathwalk(nextpath)
        except:
            return None
        
    def path_lookup(self,path):
        return self._pathwalk(path)
    
    