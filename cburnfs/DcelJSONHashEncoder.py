import json
from Dcel import Dcel
from Dcel import DcelReference
from hashlib import sha256

def dummyfunc():
    pass

class DcelJSONHashEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Dcel):
            return sha256(str(o.value).encode()).hexdigest()
        if isinstance(o, DcelReference):
            return sha256(str(o).encode()).hexdigest()
        if isinstance(o, str):
            return sha256(o.encode()).hexdigest()
        if isinstance(o, type(dummyfunc)):
            return sha256(str(o).encode()).hexdigest()
        return json.JSONEncoder.default(self,o)
    
def dumphash(o):
    _json_hash = json.dumps(o, cls=DcelJSONHashEncoder)
    return sha256(_json_hash.encode()).hexdigest()