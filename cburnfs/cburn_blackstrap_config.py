from blackstrap import BlackstrapFS
BlackstrapFS.initHost('localhost')
BlackstrapFS.addShare(
    srcaddr = 'mnt/fs',
    sharename = 'fs'
).addShare(
    srcaddr = 'mnt/fs2',
    sharename = 'fs2'
).addShare(
    srcaddr = 'mnt/fs3',
    sharename = 'fs3'
).addShare(
    srcaddr = 'mnt/fs4',
    sharename = 'fs4'
)
