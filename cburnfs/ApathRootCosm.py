from blackstrap import BlackstrapFS
from DictFS import DictFS
from HienaMP import hiena_mp
from MulticelFS import MulticelFS
from CBMetaFS import CBMetaFS
from CloudKernel import CloudKernel
from fstab_hg import fstab_hg
from cskvp_hg import cskvp_hg
from urlparse_wrapper import urlparse_wrapper
# from fs_s3fs import S3FS # removed dependency for simplicity
from fs import open_fs

# added *args, and **kwargs catch-alls
def say_hello(*args, **kwargs):
    print("hello.")
    return "hello there."

apathRootCosm = { 
    'bin': { 
        'hello': say_hello
    },
    'env': { 
        'PATH': [ 
            '.cosm/types/',
            '.cosm/tools/',
            '.cosm/bin/'
        ]
    },
    'etc': { 
        'cosmdirname': [
            '.cosm',
            '_cosm',
            '@',
            '.@',
            '_@',
        ],
        'typematch': { 
            'filefmt': {
                '.*[/]etc[/]fstab': 'fstab'
            },
            'MIME': {
                '.+[.]htm[l]?': 'text/html',
                '.+[.](txt|text)': 'text/plain',
                '.+[.]css': 'text/css',
                '.+[.][m]?js': 'text/javascript',
                # catchall
                '.*': 'application/octet-stream',
            }
        }
    },
    'kernel': CloudKernel(),
    'services': {
        'file': BlackstrapFS,
        'dict': DictFS,
        'multicel': MulticelFS,
        #'cascade' : CascadeCelFS,
        'cbmetafs': CBMetaFS,
        ## open_fs will receive a full URL with FS params url-encoded in query string. 
        # 's3': open_fs, # removed dependency for simpler installs
    },
    'tools': {
        'hiena': hiena_mp
    },
    'types': { 
        'fstab': fstab_hg,
        'cskvp': cskvp_hg,
        'url': urlparse_wrapper,
    },
    'machines': {
        'localhost': {}
    }
}
