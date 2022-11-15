from copy import deepcopy

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