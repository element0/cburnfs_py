LINE = '^[^#\n][^\n]+$'
WORD = '[^ ]+'
entryschema = [str(i) for i in range(1,10)]
fieldschema = [
    'spec', 'file', 'vfstype', 
    'mntopts', 'freq', 'passno'
]
fstab_hg = {
    "#!": ["hiena"], 
    "$__start__": "entry",
    "entry": [LINE, "field", entryschema],
    "field": [WORD, "", fieldschema]
}