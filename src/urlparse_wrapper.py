from urllib.parse import urlparse

def urlparse_wrapper(urlstr) -> dict:
    # Just in case the urlstr is a Dcel (and most likely it is)
    # urlstr is put through str().
    p = urlparse(str(urlstr))
    return { 
        'scheme':p.scheme,
        'netloc':p.netloc,
        'path':p.path,
        'params':p.params,
        'query':p.query,
        'fragment':p.fragment,
    }