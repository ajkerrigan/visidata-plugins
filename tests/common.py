from visidata import AttrDict, vd


def load_vd_sheet(inpath):
    """Load a file and return the VisiData
    sheet object.
    """
    vd.loadConfigAndPlugins(AttrDict({}))
    sheet = vd.openSource(inpath)
    sheet.reload()
    vd.sync()
    return sheet
