import re
from Dcel import Dcel

class HienaStr(str):
    def __create__(self,string,rematchobj,match_index):
        super.__create__(string)
        
    def __init__(self,string,rematchobj,match_index):
        self.hiena_data_start = rematchobj.start(match_index)
        self.hiena_data_end = rematchobj.end(match_index)
        super.__init__(string)

def hiena_mp(g:dict, text:Dcel, rulename="$__start__"):
    
    assert(type(text) is Dcel)
    
    if (type(g) is Dcel
        and type(g.value) is dict):
        g = g.value
    
    # This begins its life as a list()
    # it collects the matches for a repeating grammar rule.
    
    tree = list()
    
    # Parse a layer of `text` using current `rulename` from grammar `g`.
    
    if rulename in g:
        
        # Hook for beginning of parsing a grammar.
        # The function is recursive, so the any rule could
        # be a start rule if the function is
        # called programmatically. When APath uses HienaMP
        # as a executable interpreter, it expects $__start__. 
        
        if rulename=="$__start__":
            rulename=g["$__start__"]
        
        # If $__start__ was not specified, this is the rulename
        # called in the function args. Otherwise, it is the rulename
        # resolved from $__start__.
        
        rule = g[rulename]
        
        # all matches within `text`.
        
        m = re.finditer(rule[0], 
                        str(text),
                        re.M
                       )
        
        # next rule that parses each match in `m`.
        nextrulename = rule[1]
        
        # branch rule
        if nextrulename != "":
            for ea in m:
                
                # create fragment Dcel from `text`
                map_fragment = text[ea.start(0):ea.end(0)]
                
                # parse match and collect result in list
                tree.append(hiena_mp(
                      g,
                      # ea.group(0),    # old string version
                      map_fragment,     # new Dcel fragment version
                      nextrulename
                     ))
        
        # terminal rule
        else:
            for ea in m:
                # terminal_value = ea.group(0)  # old string version
                map_fragment = text[ea.start(0):ea.end(0)]  # new Dcel fragment version
                
                # WIP: need to attach data_map to terminal_value object
                # ie. HienaValue(ea.group(valno),ea.start(valno),ea.end(valno))
                # ie. terminal_value.data_map = data_map
                
                # tree.append(terminal_value) 
                tree.append(map_fragment)
                
        # After all matches have been recursively parsed
        # create a dictionary keyed by `labels` provided in field 2
        # of the grammar rule.
        
        # If the `labels` are a dictionary {key:number,value:number}
        # then, extract the label from the text of the match.
        
        # FIXME: validate presence of 'key' and 'value' before entering this block.
        labels = rule[2]
        if type(labels) == dict:
            keyno = labels['key']
            valno = labels['value']
            # FIXME: eleminate this double-run of the grammar
            # by caching the results earlier in the function.
            m = re.finditer(rule[0], 
                    str(text),
                    re.M
                   )
            
            # HACK to populate empty Key-val-pairs with something useful.
            # This should propogate back to the underlier correctly.
            if(ea.start(valno) == -1):
                valno = keyno
            # end HACK
            tree = { ea.group(keyno):text[ea.start(valno):ea.end(valno)]
                    # WIP: need to attach data_map to terminal_value object
                    # ie. HienaValue(ea.group(valno),ea.start(valno),ea.end(valno))
                    for ea in m
                   }
            # WIP: need to attach a data_map to the tree
            # ie. tree.data_map
            return tree
        else:        
            tree = { k:v for k,v 
                    in zip(labels, 
                           tree
                          )}
        return tree