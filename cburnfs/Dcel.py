from fs.base import FS
from fs.info import Info
from fs.errors import NoURL, InvalidPath, ResourceNotFound, DirectoryExpected
from fs.path import normpath
from inspect import isclass, isfunction, ismethod
from urllib.parse import urlparse
from mergeinfo import mergeinfo
from ValueSvc import ValueSvc

DEFAULT_HOST = 'localhost'

class DcelReference:
    def __init__(self,dcel):
        self._dcel = dcel
        
    def __invert__(self):
        return self._dcel
    
    def __str__(self):
        return str(self._dcel)
    
class DcelIterator:
    """WIP: Don't use this yet. Dcel::__iter__() should return an iterator derived from Dcel::value"""
    def __init__(self,target):
        if target != None:
            self.target = target
            self.curpos = 0
        
    def __iter__(self):
        return self
    
    def __next__():
        raise StopIteration
        

class Dcel(FS):
    
    def __new__(cls, arg1=None, *args, **kwargs):
        if type(arg1) is Dcel:
            if 'writeable' in kwargs:
                # This allows cloning a new Dcel
                # from an old one, with a different `writeable`
                # property.
                if kwargs['writeable'] != arg1._writeable:
                    return super().__new__(cls)
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
                 writeable = True,
                ):
        """
        Initialize a new Dcel object.
        
        If self.__inited == True, then we are unwrapping the 
        dcel from a wrapper, and no initialization is needed.
        
        These are the main pathways:
        - address only (expected to use as a value)
        - address and service
        - address and service_class
        - slice
        """
        # __inited
        try:
            """
            The Apath
            class might be unwrapping
            an Apath from a wrapper.
            """
            if self.__inited == True:
                return
        except AttributeError:
            # a new instance.
            super().__init__()
            self.__inited = True
        
        # _writable
        # Note to future self:
        # Don't set _writeable until end of initialization
        # or you are in for a city-state of pain.
        # Example: `self._writeable = writeable`
        # DO the sensible thing.
        self._writeable = True
        # And then please remember to set the actual value
        # before the method returns.
        
        # If the address is a dcel,
        # use the dcel's value
        # and save the dcel in case
        # it needs to be re-evaluated.
        
        def init_address_only(address):
            if type(address) is Dcel:
                # Clone a Dcel but
                # allow current __init__() to override 'writeable' property.
                try:
                    self.address = address.address
                except:
                    self.address = address.value
                try:
                    self.service = address.service
                except:
                    pass
            elif issubclass(type(address),(str,int,bool)):
                self.address = '.'
                self.service = ValueSvc(address)
        
        def init_address_service(address, service):
            self.address = address
            self.service = service
        
        def init_address_service_class(address,
                                       service_class,
                                       args=None,
                                       kwargs=None
                                      ):
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
        
        # NEW switch to init
        # - pathway: address only
        if ( address and
             not service and
             not formula and
             not args and
             not value and
             not service_class and
             not service_args and
             not kwargs
             # writeable will be processed at the end of __init__()
           ):
            init_address_only(address)
        # - pathway: address and service
        elif ( address and service and
             not formula and
             not args and
             not value and
             not service_class and
             not service_args and
             not kwargs
             # writeable will be processed at the end of __init__()
           ):
            init_address_service(address, service)
        # - pathway: address and service_class
        elif ( address and service_class and
             not service and
             not formula and
             not value
             # (optional) args
             # (optional) service_args
             # (optional) kwargs
             # writeable will be processed at the end of __init__()
           ):
            init_address_service_class(address,
                                       service_class,
                                       *(args if args else []),
                                       *(service_args if service_args else []),
                                       # args and service_args will be concatenated
                                       # if received with *args signature.
                                       **(kwargs if kwargs else {})
                                      )
                
        # Deprecate Dcel formula parameter
        # in favor of FormulaFS service_class
        if formula and args:
            self.formula = formula
            self.args    = args
            self.kwargs  = kwargs
        elif formula:
            self.formula = formula
            
        # Value
        if not value is None:
            self.value = value
            
        
        # internal stubs
        self._map = None
        self._dir = None
        
        # last word
        # (Thank you for keeping this here, as it must be.)
        self._writeable = writeable
        
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
                return _value
            else:
                _value = str(self.service.preslice_value())[self.address]
                return _value
            
        # value from service.value
        if (hasattr(self,'service')
            and hasattr(self.service,'value')):
            return self.service.value
        
        # value from readtext
        try:
            _value = self.readtext('.')
            self._value = _value
        except:
            try:
                _value = self.readbytes('.')
                self._value = _value
            except:
                pass
        
        # value from formula
        # DEV: Depricating in favor of FormulaFS service_class.
        try:
            # the dirty flag becomes available
            # the first time self.value is set.
            if not hasattr(self,'_dirty'):
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
                try:
                    _value = self.formula(*_args,**_kwargs)
                    self.value = _value
                    return _value
                except:
                    pass
            else:
                # return buffer
                if hasattr(self._value):
                    return self._value
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
        
        def set_dirty():
            # if this is a subsequent time
            if hasattr(self,'_dirty'):
                self._dirty = True
                
            # if this is the first time
            if not hasattr(self,'_dirty'):
                self._dirty = False
        
        if self._writeable == False:
            raise Exception('not writeable')
        
        # set buffer if contents changed
        if not hasattr(self,'_value'):
            self._value = new_value
            set_dirty()
        elif self._value != new_value:
            self._value = new_value
            set_dirty()
            
        
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
            return Dcel(address=key,service=self,writeable=self._writeable)
        # before adding a _dir,
        # does the service see this
        # base address (not the key) as a dir?
        
        # WIP Dcel address
        # convert Dcel value to string type
        if (type(key) is Dcel):
            key = str(key)
        
        # function?
        if hasattr(self, 'formula'):
            raise DirectoryExpected('Formula cell has no directory.')
        
        # indexed or iterable?
        if (not hasattr(self,'address')
           and not hasattr(self,'service')
           and (hasattr(self.value,'__getitem__'
                or hasattr(self.value,'__iter__')))):
            if key in ['/','.','']:
                return self
            return Dcel(self.value[key])

        # testing base address for dir
        if not self.service.isdir(self.address):
            pass
            #raise TypeError(self.address)

        # base address of this Dcel is a directory
        # now we can look up the key.

        if not type(self._dir) is dict:
            # self._dir is not dict
            basepath = self.address
            if basepath == '/':
                basepath = ''
            # create address ("path") of key relative to service
            if type(basepath) is str:
                path = basepath + '/' + key.lstrip('/')
            else:
                path = key.lstrip('/')
            if self.service.exists(path):
                # create Dcel's internal _dir and add child
                child = Dcel(address=path,
                             service=self.service,
                             writeable=self._writeable
                            )
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
            if key == None:
                path = basepath
            else:
                path = basepath + '/' + key.lstrip('/')
            if self.service.exists(path):
                # child
                child = Dcel(address=path,
                            service=self.service,
                             writeable=self._writeable
                            )
                self._dir[key] = child
                return child
            else:
                raise KeyError(key)
        except TypeError:
            raise TypeError(self._dir)
            
    def __setitem__(self,key,value):
        if self._writeable == False:
            raise Exception('not writeable')
        self[key].value = value
        
    def __iter__(self):
        """Return an iterator derived from `self.value`.
        
        If self.value is a string, just return an iterator
        of a list with that string as a single element.
        """
        if (hasattr(self.value,'__iter__')
            and self.value.__iter__ != None):
            if type(self.value) != str:
                return self.value.__iter__()
            else:
                return [self.value].__iter__()
    
        
    def keys(self):
        if hasattr(self,'service'):
            return self.listdir('.')
        if hasattr(self.value,'keys'):
            return self.value.keys()
        else:
            return None
            

    
    # Info helpers
    
    ## Absolute path.
    #  Be _very_ careful modifying this.
    #  Because there are potentially different object
    #  types which can be used for the address,
    #  _especially_ `slice` objects, we can't really modify
    #  anything but 'pathlike' objects, which have
    #  string representations.
    def abspath(self, addr=None):
        if hasattr(self,'address'):
            _self_address = self.address
        else:
            _self_address = ''
        if type(addr) is str:
            if not addr in ['/','.','']:
                if _self_address == '':
                    return _self_address + '/' + addr.lstrip('/')
                else:
                    return addr
            else:
                if hasattr(self,'address'):
                    return self.address
                return addr
        if addr != None:
            return addr
        else:
            return _self_address
    
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
        try:
            rooturl = self.service.__rooturl
        except:
            rooturl = None
        if not type(rooturl) is str:
            rooturl = None
        if not rooturl is None:
            hostinfo = { 'hosts': [rooturl] }
            raw = mergeinfo(info.raw, hostinfo)
        else:
            raw = info.raw
        return Info(raw)
    
    def listdir(self,path=None):
        if hasattr(self, 'service'):
            path = self.abspath(path)
            return self.service.listdir(path)
    
    def isdir(self,path=None):
        
        if hasattr(self, 'service'):
            _path = self.abspath(path)
            return self.service.isdir(_path)
        
        _value = self.value
        if (hasattr(_value,'__getitem__')
            and not type(_value) is str):
            try:
                # Dcel will respond to __getitem__
                # so we need to see if iter() works.
                res = iter(_value)
                return True
            except:
                return False
        else:
            return False

    def openbin(self,
            path=None,
            mode='r',
            buffering=-1,
            **options):
        # Open a binary file.
        path = self.abspath(path)
        if self._writeable == False:
            mode='r'
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
    
    def setinfo(self,path,info):
        if self._writeable == False:
            raise Exception('not writeable')
        path = self.abspath(path)
        return self.service.setinfo(path,info)

    def makedir(self,*args,**kwargs):
        if self._writeable == False:
            raise Exception('not writeable')
        return self.service.makedir(*args,**kwargs)
        
    def remove(self,*args,**kwargs):
        if self._writeable == False:
            raise Exception('not writeable')
        self.service.remove(*args,**kwargs)
        
    def removedir(self,*args,**kwargs):
        if self._writeable == False:
            raise Exception('not writeable')
        self.service.removedir(*args,**kwargs)
        
    def writetext(self, path=None, contents='', encoding='utf-8',
                  errors=None, newline=''):
        if self._writeable == False:
            raise Exception('not writeable')
        path = self.abspath(path)
        self.service.writetext(path,contents,encoding,errors,newline)

    ### Additional Methods
    
    def _pathwalk(self,path):
        if path in ['/', '.', '', None]:
            return self
        try:
            seg,nextpath = path.split('/',1)
        except:
            return self[path]
        try:
            if seg in ['/', '.', '']:
                target = self
            else:
                target = self[seg]
        except:
            raise ResourceNotFound(seg)
        try:
            return target._pathwalk(nextpath)
        except:
            raise ResourceNotFound(nextpath)
        
    def path_lookup(self,path):
        try:
            return self._pathwalk(path)
        except:
            raise
    
    ### Custom Request Processing
    
    def processRequest(self,path,rq):
        if hastattr(self.service,"processRequest"):
            try:
                response = self.service.processRequest(path,rq)
            except Exception as e:
                return {'Dcel::processRequest':{'service error':str(e)}}
            return response
    
    def inspect(target):
        if not target:
            return "Target was empty. Nothing to inspect."
        if hasattr(target, "address"):
            _address = target.address
            _address_type = type(target.address)
            _abspath = target.abspath(target.address)
            _abspath_type = type(_abspath)
        else:
            _address = ''
            _address_type = 'Address attribute not present.'
            _abspath = target.abspath(None)
            _abspath_type = 'Abspath calulated from `None`.'
        if hasattr(target, "service"):
            _service = target.service
            _service_type = type(target.service)
        else:
            _service = ''
            _service_type = 'Service attribute not present.'
        # Note to self: `service_class` is an `__init__()` keword arg
        # which resolves to the `.service` attribute during `__init__()`.
        if hasattr(target,"value"):
            _value = target.value
            _value_type = type(target.value)
        else:
            _value = ''
            _value_type = 'Value not present.'
        if hasattr(target,"_map"):
            _map = target._map
            _map_type = type(target._map)
        else:
            _map = ''
            _map_type = '_map not present.'
        if hasattr(target,"_dir"):
            _dir = target._dir
            _dir_type = type(target._dir)
        else:
            _dir = ''
            _dir_type = 'Dir not present.'

        return f"""address: {_address_type}:{_address}
        abspath: {_abspath_type}:{_abspath}
        service: {_service_type}:{_service}
        value: {_value_type}:{_value}
        _map: {_map_type}:{_map}
        _dir: {_dir_type}:{_dir}
        """
