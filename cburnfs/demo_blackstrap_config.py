from blackstrap import BlackstrapFS
BlackstrapFS.initHost('localhost')
BlackstrapFS.addShare(
    srcaddr = 'demo-files/fs',
    sharename = 'fs'
).addShare(
    srcaddr = 'demo-files/fs2',
    sharename = 'fs2'
).addShare(
    srcaddr = 'demo-files/fs3',
    sharename = 'fs3'
).addShare(
    srcaddr = 'demo-files/fs4',
    sharename = 'fs4'
)
