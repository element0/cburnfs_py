'''This is a dud Redis to be swapped in wherever
   you don't want to use an actual Redis implementation
   because of your constraints.
'''
class Redis:
    def __init__(self,
                 host='localhost',
                 port=6379,
                 db=0):
        self.host_dud = host
        self.port_dud = port
        self.db_dud = db
        self._dict = dict()

    def set(self, name, value):
        self._dict[name] = value

    def get(self, name):
        if name in self._dict:
            return self._dict[name]
        else:
            return None
        
    def delete(self, *names):
        for name in names:
            if name in self._dict:
                del self._dict[name]

    def incr(self, name, amount=1):
        if name in self._dict:
            val = int(self._dict[name])
            val = val + amount
            self._dict[name] = val
            return val
        else:
            self._dict[name] = amount
            return amount

    def keys(self, pattern = '*', **kwargs):
        '''(Should) return a list of keys matching ``pattern``'''
        if pattern == '*':
            return list(self._dict.keys())
                
