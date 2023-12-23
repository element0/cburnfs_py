from APath import APath
from MulticelFS import MulticelFS

class CosmosShell(APath):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        
    def lookup(self, addr):
        if addr in self.cosm.listdir('/etc/cosmdirname'):
            _targ1 = super().lookup(addr)
            if self.parent:
                _parent_cosm = self.parent.cosm
            else:
                _parent_cosm = APath._rootcosm
            _cosmstack = [Dcel(_parent_cosm,writeable=False),
                          Dcel(_targ1.target,writeable=True)]
            _overlay = Dcel(_cosmstack, service_class=MulticelFS)
            return APath(_overlay)
        return super().lookup(addr)
    
    def new(self, dirent_name='', typename='', **kwargs):
        return None
    