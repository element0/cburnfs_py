import json
from Dcel import Dcel

def dummyfunc():
    pass

class DcelJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Dcel):
            return o.value
        if isinstance(o, type(dummyfunc)):
            return str(o)
        return json.JSONEncoder.default(self,o)
    
def dumpdcel(o):
    return json.dumps(o, cls=DcelJSONEncoder)