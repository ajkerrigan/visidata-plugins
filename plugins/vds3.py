'''
Allow VisiData to work directly with Amazon S3 paths. Functionality
is more limited than local paths, but supports:

* Navigating among directories (S3 prefixes)
* Opening supported filetypes, including compressed files
'''

from functools import lru_cache

from s3fs import S3FileSystem

from visidata import (
    ENTER,
    Column,
    Path,
    Sheet,
    asyncthread,
    date,
    error,
    getGlobals,
    status,
    warning,
)


class S3Path(Path):
    '''
    A Path-like object representing an S3 file (object) or directory (prefix).
    '''

    # Ideally we want to create a filesystem object once, then reuse it for
    # subsequent S3 operations across any number of paths. Setting up a cache
    # here enables that.
    fs = lru_cache()(S3FileSystem)

    def __init__(self, path):
        super().__init__(path)
        self.fs = self.__class__.fs()
        self.given = path

    def open(self, *args, **kwargs):
        '''
        Open the current S3 path, decompressing along the way if needed.
        '''
        fp = self.fs.open(self.given)

        if self.compression == 'gz':
            import gzip

            return gzip.open(fp, *args, **kwargs)

        if self.compression == 'bz2':
            import bz2

            return bz2.open(fp, *args, **kwargs)

        if self.compression == 'xz':
            import lzma

            return lzma.open(fp, *args, **kwargs)

        return fp

    def exists(self):
        '''
        Return true if this S3 path is an existing directory (prefix)
        or file (object).
        '''
        return self.fs.exists(str(self.given))

    def is_dir(self):
        '''
        Return True if this S3 path is a directory (prefix).
        '''
        return self.fs.isdir(str(self.given))


class S3DirSheet(Sheet):
    '''
    Display a listing of files and directories (objects and prefixes) in an S3 path.
    Allow single or multiple entries to be opened in separate sheets.
    '''

    rowtype = 'files'
    columns = [
        Column('name', getter=lambda col, row: row.get('Key').rpartition('/')[2]),
        Column('type', getter=lambda col, row: row.get('type')),
        Column('size', type=int, getter=lambda col, row: row.get('Size')),
        Column('modtime', type=date, getter=lambda col, row: row.get('LastModified')),
    ]
    nKeys = 1

    @asyncthread
    def reload(self):
        '''
        Refreshes the current S3 directory (prefix) listing. Forces a refresh from
        the S3 filesystem, to avoid using cached responses and missing recent changes.
        '''

        self.reset()  # reset deferred caches
        basepath = str(self.source)
        self.rows = [
            entry for entry in self.source.fs.ls(basepath, detail=True, refresh=True)
        ]


S3DirSheet.addCommand(
    ENTER, 'open-row', 'vd.push(openSource("s3://{}".format(cursorRow["Key"])))'
)
S3DirSheet.addCommand(
    'g' + ENTER,
    'open-rows',
    'for r in selectedRows: vd.push(openSource("s3://{}".format(r["Key"])))',
)


def openurl_s3(p, filetype):
    '''
    Open a sheet for an S3 path. S3 directories (prefixes) require special handling,
    but files (objects) can use standard VisiData "open" functions.
    '''

    p = S3Path(p.url)
    if not p.exists():
        error('"%s" does not exist, and creating S3 files is not supported' % p.given)

    if not filetype:
        filetype = p.ext or 'txt'

    if p.is_dir():
        return S3DirSheet(p.name, source=p)

    openfunc = 'open_' + filetype.lower()
    if openfunc not in getGlobals():
        warning('no %s function' % openfunc)
        filetype = 'txt'
        openfunc = 'open_txt'

    vs = getGlobals()[openfunc](p)
    status('opening %s as %s' % (p.given, filetype))
    return vs
