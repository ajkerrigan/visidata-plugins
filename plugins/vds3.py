'''
Allow VisiData to work directly with Amazon S3 paths. Functionality
is more limited than local paths, but supports:

* Navigating among directories (S3 prefixes)
* Opening supported filetypes, including compressed files
'''

from visidata import (
    ENTER,
    Column,
    Path,
    Sheet,
    VisiData,
    addGlobals,
    asyncthread,
    date,
    error,
    getGlobals,
    open_txt,
    option,
    options,
    status,
    vd,
    warning,
)

__version__ = '0.4'

option(
    'vds3_endpoint',
    '',
    'alternate S3 endpoint, used for local testing or alternative S3-compatible services',
    replay=True,
)
option('vds3_glob', True, 'enable glob-matching for S3 paths', replay=True)


class S3Path(Path):
    '''
    A Path-like object representing an S3 file (object) or directory (prefix).
    '''

    fs = None

    def __init__(self, path):
        super().__init__(path)
        self.given = path

    def open(self, *args, **kwargs):
        '''
        Open the current S3 path, decompressing along the way if needed.
        '''

        # Default to text mode unless we have a compressed file
        mode = 'rb' if self.compression else 'r'

        fp = self.fs.open(self.given, mode=mode)

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

    def glob(self):
        '''
        Perform glob-matching against this path.
        '''
        return self.fs.glob(str(self.given))

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

    def __init__(self, name, source):
        super().__init__(name=name, source=source)
        self.rowtype = 'files'
        self.nKeys = 1

    @staticmethod
    def object_display_name(col, row):
        return row.get('Key').rpartition('/')[2]

    @asyncthread
    def loadRows(self):
        # Add rows one at a time here, as plugins may hook into addRow.
        self.rows = []
        for entry in self.source.fs.ls(str(self.source), detail=True, refresh=True):
            self.addRow(entry)

    @asyncthread
    def reload(self):
        '''
        Refresh the current S3 directory (prefix) listing. Force a refresh from
        the S3 filesystem to avoid using cached responses and missing recent changes.
        '''
        self.columns = []
        for col in (
            Column('name', getter=self.__class__.object_display_name),
            Column('type', getter=lambda col, row: row.get('type')),
            Column('size', type=int, getter=lambda col, row: row.get('Size')),
            Column(
                'modtime', type=date, getter=lambda col, row: row.get('LastModified')
            ),
        ):
            self.addColumn(col)

        self.loadRows()


class S3GlobSheet(S3DirSheet):
    '''
    A listing of S3 objects matching a given glob pattern. Display full
    key names rather than S3DirSheet's "directory-browsing" behavior.
    Allow single or multiple entries to be opened in separate sheets.
    '''

    @staticmethod
    def object_display_name(col, row):
        return row.get('Key')

    @asyncthread
    def loadRows(self):
        # Add rows one at a time here, as plugins may hook into addRow.
        self.rows = []
        for entry in self.source.fs.glob(str(self.source), refresh=True):
            self.addRow(self.source.fs.stat(entry))


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
    import re
    from s3fs import S3FileSystem

    if not S3Path.fs:
        endpoint = options.vds3_endpoint
        S3Path.fs = S3FileSystem(
            client_kwargs=({'endpoint_url': endpoint} if endpoint else None)
        )

    p = S3Path(p.given)

    if options.vds3_glob and re.search(r'[*?\[\]]', p.given):
        return S3GlobSheet(p.name, source=p)

    if not p.exists():
        error(f'"{p.given}" does not exist, and creating S3 files is not supported')

    if p.is_dir():
        return S3DirSheet(p.name, source=p)

    if not filetype:
        filetype = p.ext or 'txt'

    openfunc = getGlobals().get('open_' + filetype.lower())
    if not openfunc:
        warning(f'no loader found for {filetype} files, falling back to txt')
        filetype = 'txt'
        openfunc = open_txt

    vs = openfunc(p)
    status(f'opening {p.given} as {filetype}')
    return vs


addGlobals(globals())
