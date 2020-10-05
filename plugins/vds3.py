'''
Allow VisiData to work directly with Amazon S3 paths. Functionality
is more limited than local paths, but supports:

* Navigating among directories (S3 prefixes)
* Opening supported filetypes, including compressed files
* Versioned buckets
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
    vd,
)

__version__ = '0.4'

vd.option(
    'vds3_endpoint',
    '',
    'alternate S3 endpoint, used for local testing or alternative S3-compatible services',
    replay=True,
)
vd.option('vds3_glob', True, 'enable glob-matching for S3 paths', replay=True)
vd.option(
    'vds3_version_aware',
    False,
    'show all object versions in a versioned bucket',
    replay=True,
)


class S3Path(Path):
    '''
    A Path-like object representing an S3 file (object) or directory (prefix).
    '''

    _fs = None

    def __init__(self, path, version_aware=None, version_id=None):
        super().__init__(path)
        self.given = path
        self.version_aware = version_aware or vd.options.vds3_version_aware
        self.version_id = self.version_aware and version_id or None

    @property
    def fs(self):
        from s3fs.core import S3FileSystem

        if self._fs is None:
            self._fs = S3FileSystem(
                client_kwargs={'endpoint_url': vd.options.vds3_endpoint or None},
                version_aware=self.version_aware,
            )

        return self._fs

    @fs.setter
    def fs(self, val):
        self._fs = val

    def open(self, *args, **kwargs):
        '''
        Open the current S3 path, decompressing along the way if needed.
        '''

        # Default to text mode unless we have a compressed file
        mode = 'rb' if self.compression else 'r'

        fp = self.fs.open(self.given, mode=mode, version_id=self.version_id)

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


class S3DirSheet(Sheet):
    '''
    Display a listing of files and directories (objects and prefixes) in an S3 path.
    Allow single or multiple entries to be opened in separate sheets.
    '''

    def __init__(self, name, source, version_aware=None):
        import re

        super().__init__(name=name, source=source)
        self.rowtype = 'files'
        self.nKeys = 1
        self.use_glob_matching = vd.options.vds3_glob and re.search(
            r'[*?\[\]]', self.source.given
        )
        self.version_aware = (
            vd.options.vds3_version_aware if version_aware is None else version_aware
        )
        self.fs = source.fs

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
        list_func = self.fs.glob if self.use_glob_matching else self.fs.ls

        for key in list_func(str(self.source)):
            if self.version_aware and self.fs.isfile(key):
                yield from (
                    {**version_info, 'Key': key, 'type': 'file'}
                    for version_info in self.fs.object_version_info(key)
                )
            else:
                yield self.fs.stat(key)

    @asyncthread
    def reload(self):
        '''
        Reload the current S3 directory (prefix) listing.
        '''
        self.columns = []

        if not (
            self.use_glob_matching
            or self.fs.exists(self.source.given)
            or self.fs.isdir(self.source.given)
        ):
            error(f'unable to open S3 path: {self.source.given}')

        for col in (
            Column('name', getter=self.object_display_name),
            Column('type', getter=lambda _, row: row.get('type')),
            Column('size', type=int, getter=lambda _, row: row.get('Size')),
            Column('modtime', type=date, getter=lambda _, row: row.get('LastModified')),
        ):
            self.addColumn(col)

        if self.version_aware:
            self.addColumn(
                Column('latest', type=bool, getter=lambda _, row: row.get('IsLatest'))
            )
            self.addColumn(
                Column(
                    'version_id',
                    type=str,
                    getter=lambda _, row: row.get('VersionId'),
                    width=0,
                )
            )

        super().reload()

    def refresh(self, path=None):
        '''
        Clear the s3fs cache for the given path and reload. By default, clear
        the entire cache.
        '''
        self.fs.invalidate_cache(path)
        self.reload()

    def toggle_versioning(self):
        '''
        Enable or disable support for S3 versioning.
        '''
        self.version_aware = not self.version_aware
        self.fs.version_aware = self.version_aware
        vd.status(f's3 versioning {"enabled" if self.version_aware else "disabled"}')
        self.reload()


def openurl_s3(p, filetype, version_aware=None, version_id=None):
    '''
    Open a sheet for an S3 path. S3 directories (prefixes) require special handling,
    but files (objects) can use standard VisiData "open" functions.
    '''

    # Non-obvious behavior here: For the default case, we don't want to send
    # a custom endpoint to s3fs. However, using None as a default trips up
    # VisiData's type detection for the endpoint option. So we use an empty
    # string as the default instead, and convert back to None here.
    endpoint = vd.options.vds3_endpoint or None

    p = S3Path(
        str(p.given),
        version_aware=version_aware or vd.options.vds3_version_aware,
        version_id=version_id,
    )

    p.fs.version_aware = p.version_aware
    if p.fs.client_kwargs.get('endpoint_url', '') != endpoint:
        p.fs.client_kwargs = {'endpoint_url': endpoint}
        p.fs.connect()

    if not p.fs.isfile(str(p.given)):
        return S3DirSheet(p.name, source=p, version_aware=p.version_aware)

    if not filetype:
        filetype = p.ext or 'txt'

    openfunc = getGlobals().get('open_' + filetype.lower())
    if not openfunc:
        vd.warning(f'no loader found for {filetype} files, falling back to txt')
        filetype = 'txt'
        openfunc = open_txt

    vs = openfunc(p)
    vd.status(
        f'opening {p.given} as {filetype} (version id: {p.version_id or "latest"})'
    )
    return vs


S3DirSheet.addCommand(
    ENTER,
    'open-row',
    'vd.push(openSource(S3Path("s3://{}".format(cursorRow["Key"]), version_aware=sheet.version_aware, version_id=cursorRow.get("VersionId"))))',
    'open the current S3 entry',
)
S3DirSheet.addCommand(
    'g' + ENTER,
    'open-rows',
    'for r in selectedRows: vd.push(openSource("s3://{}".format(r["Key"]), version_aware=sheet.version_aware, version_id=cursorRow.get("VersionId")))',
    'open all selected S3 entries',
)
S3DirSheet.addCommand(
    'z^R',
    'refresh-sheet',
    'sheet.refresh(str(sheet.source))',
    'clear the s3fs cache for this path, then reload',
)
S3DirSheet.addCommand(
    'gz^R',
    'refresh-sheet-all',
    'sheet.refresh()',
    'clear the entire s3fs cache, then reload',
)
S3DirSheet.addCommand(
    '^V',
    'toggle-versioning',
    'sheet.toggle_versioning()',
    'enable/disable support for S3 versioning',
)

addGlobals(globals())
