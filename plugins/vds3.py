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
    addGlobals,
    asyncthread,
    date,
    error,
    getGlobals,
    open_txt,
    option,
    options,
    status,
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

    def is_file(self):
        '''
        Does this path represent a file?
        '''
        return self.fs.isfile(str(self.given))


class S3DirSheet(Sheet):
    '''
    Display a listing of files and directories (objects and prefixes) in an S3 path.
    Allow single or multiple entries to be opened in separate sheets.
    '''

    def __init__(self, name, source):
        super().__init__(name=name, source=source)
        self.rowtype = 'files'
        self.nKeys = 1
        self.use_glob_matching = options.vds3_glob

    def object_display_name(self, _, row):
        '''
        Provide a friendly display name for an S3 path.

        When listing the contents of a single S3 prefix, the name can chop off
        prefix bits to imitate a directory browser. When glob matching,
        include the full key name for each entry.
        '''
        return (
            row.get('Key')
            if self.use_glob_matching
            else row.get('Key').rpartition('/')[2]
        )

    def iterload(self):
        '''
        Delegate to the underlying filesystem to fetch S3 entries.
        '''
        row_data = (
            (
                self.source.fs.stat(entry)
                for entry in self.source.fs.glob(str(self.source), refresh=True)
            )
            if self.use_glob_matching
            else self.source.fs.ls(str(self.source), detail=True, refresh=True)
        )
        yield from row_data

    @asyncthread
    def reload(self):
        '''
        Refresh the current S3 directory (prefix) listing. Force a refresh from
        the S3 filesystem to avoid using cached responses and missing recent changes.
        '''
        import re

        self.columns = []
        self.use_glob_matching = self.options.vds3_glob and re.search(
            r'[*?\[\]]', self.source.given
        )

        if not (self.use_glob_matching or self.source.fs.exists(self.source.given)):
            error(f'unable to open S3 path: {self.source.given}')

        for col in (
            Column('name', getter=self.object_display_name),
            Column('type', getter=lambda _, row: row.get('type')),
            Column('size', type=int, getter=lambda _, row: row.get('Size')),
            Column(
                'modtime', type=date, getter=lambda _, row: row.get('LastModified')
            ),
        ):
            self.addColumn(col)

        super().reload()


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
    from s3fs import S3FileSystem

    # Non-obvious behavior here: For the default case, we don't want to send
    # a custom endpoint to s3fs. However, using None as a default trips up
    # VisiData's type detection for the endpoint option. So we use an empty
    # string as the default instead, and convert back to None here.
    endpoint = options.vds3_endpoint or None
    version_aware = options.vds3_version_aware

    # We can reuse an existing S3FileSystem as long as no relevant options
    # have changed since it was created.
    if (
        not S3Path.fs
        or S3Path.fs.version_aware != version_aware
        or S3Path.fs.client_kwargs.get('endpoint_url', '') != endpoint
    ):
        S3Path.fs = S3FileSystem(
            client_kwargs={'endpoint_url': endpoint}, version_aware=version_aware
        )

    p = S3Path(p.given)

    if not p.is_file():
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
