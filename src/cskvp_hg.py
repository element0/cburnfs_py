LINE = '^[^#\n][^\n]+$'
CSKVP = '([^, =]+)(?:[=]([^, =]+))?'

numschema = [str(i) for i in range(1,10)]
kvpschema = {'key':1, 'value':2}
    
cskvp_hg = {
    "#!": ["hiena"], 
    "$__start__": "cskvp",
    # "row": [LINE, "cskvp", numschema],
    "cskvp": [CSKVP, "", kvpschema]
}