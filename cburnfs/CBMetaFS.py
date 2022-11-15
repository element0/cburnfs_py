#!/usr/bin/env python
# coding: utf-8

# # CBMetaFS
# 
# Cloudburner Metadata FS
# 
# 0.2
# There are RW issues when using a zip file. The workaround is to use a temp overlay for writing.
# 
# 0.3
# The benefit of zip is compression. But meta storage was complicated by using directory structures because they can't naturally store metadata for _directories_ themselves without creating extra files. The metafs storage is now just a kyotocabinet-style associative array (dict) that maps whole-path strings to dictionaries. This `infostore` is exported as a json file within the zip container.

# In[2]:


from fs.zipfs import ZipFS
from fs.tempfs import TempFS
from fs.multifs import MultiFS
from fs.osfs import OSFS
from fs.base import FS
from fs.info import Info
from fs.errors import ResourceNotFound, CreateFailed
from os.path import exists, split, join
from os import rename
import json
import six

class CBMetaFS(FS):
    
    version = 0.3
    """
    0.3 Flat path array format
    write meta to paths with / segs
    write meta to directories
    todo: remove obsoleted code
    todo: fix ignored exception on close
    
    0.2 Fixed complaint on close. 
    """
    
    def __init__(self, path):
        self.path = path
        self.writepath = path + "_appending"
        
        self.dirname,        self.filename = split(path)
        
        self.infostore = dict()
            
        if exists(path):
            self.tmpname = self.filename + '_tmp'
            
            m = MultiFS()
            m.add_fs('readfrom',
                     ZipFS(path))
            m.add_fs('writeto',
                     TempFS(
                         identifier=self.tmpname,
                         temp_dir=self.dirname
                     ),
                     write=True
                    )
            
            self._fs = ZipFS(
                self.writepath,
                write=True,
                temp_fs=m
            )
            
            
            try:
                with self._fs.open("infostore.json") as metarecord:
                    self.infostore = json.load(metarecord)
            except ResourceNotFound:
                raise
            except json.JSONDecodeError:
                raise ResourceNotFound
            
        else:
            try:
                self._fs = ZipFS(
                    self.writepath,
                    write=True)
            except CreateFailed as er:
                self._fs = None
                print(er)
            
        
    def _close(self):
        if not self._fs == None:
            with self._fs.open('infostore.json', mode='w') as metarecord:
                json.dump(self.infostore,
                          metarecord) 
            
            self._fs.close()
            if exists(self.writepath):
                rename(
                    self.writepath,
                    self.path
                )
        
    if six.PY2:
        def close(self):  # noqa: D102
            self._close()
            super(CBMetaFS, self).close()
            
    else:
        def close(self): # noqa: D102
            self._close()
            super().close()
    
    
    def _getinfo1(self, path, namespaces=None): # Get info regarding a file or directory.
        """
        Gets metadata stored as contents
        of a file inside a ZipFS.
        """
        try:
            with self._fs.open(path) as metarecord:
                raw = json.load(metarecord)
                i = Info(raw)
        except ResourceNotFound:
            i = None
            raise
        except json.JSONDecodeError:
            raise ResourceNotFound
            
        return i
    
    def _getinfo2(self, path, namespaces=None):
        if path in self.infostore:
            return Info(self.infostore[path])
        else:
            return Info(dict())
    
    def getinfo(self, path, namespaces=None):
        return self._getinfo2(path, namespaces)
    
    def listdir(self,path): # Get a list of resources in a directory.
        return list()
    
    def makedir(self,path, permissions=None, recreate=False): # Make a directory.
        subpath = ""
        return SubFS(self,subpath)
    
    def openbin(self, path, mode='r', buffering=-1, **options): # Open a binary file.
        return CloudburnerFile()
    
    def remove(self,path): # Remove a file.
        return 
    
    def removedir(self,path): # Remove a directory.
        pass
    
    def _setinfo2(self,path,info):
        self.infostore[path] = info
        
    
    def _setinfo1(self,path,info): # Set resource information.
        """
        Gets metadata stored as contents
        of a file inside a ZipFS.
        """
        try:
            with self._fs.open(path, mode='w') as metarecord:
                json.dump(info,metarecord)
        except ResourceNotFound:
            raise
        except json.JSONDecodeError:
            raise
            
    def setinfo(self,path,info):
        self._setinfo2(path,info)
        


# In[3]:


#from CBMetaFS import CBMetaFS

def testCBMetaFS():
    with CBMetaFS('testMetaFS') as mfs:
        mfs.setinfo('colors/blue',{"cburn":{"hosts":["buckbean.com","localhost"]}})

    with CBMetaFS('testMetaFS') as mfs:
        i = mfs.getinfo('colors/blue')
        print(i.raw)


        


# In[6]:



    
class CBMetaData():
    
    def __init__(self,metaList = dict()):
        self.meta = metaList
        
    def get(self,path) -> dict:
        if path in self.meta:
            return self.meta[path].data;
        else:
            return None
    
    def put(self,path,data={}) -> dict:
        self.meta[path] = CBMetaUnit(data)
        
        return data
    
    # webdav style updaters
    def propertyupdate(self,path,uprq):
        if path in self.meta:
            munit = self.meta[path]
        else:
            self.put(path)
            munit = self.meta[path]
        
        for verb in uprq:
            if verb == 'append':
                munit.append(uprq[verb])
            if verb == 'remove':
                munit.remove(uprq[verb])
        
        print('propertyupdate: '+json.dumps(munit.data))
        
        return munit
    
    def processRequest(self,path,rq):
        response = dict()
        for mod in rq:
            if mod == 'propertyupdate':
                response[mod] = self.propertyupdate(path,rq[mod])
            
        return response

