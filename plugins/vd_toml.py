from visidata import (
    vd,
    VisiData,
    PyobjSheet,
)

try:
    # This will work in Python 3.11+
    import tomllib
except ModuleNotFoundError:
    # Fallback for Python 3.10 and below
    import tomli as tomllib


@VisiData.api
def open_toml(vd, p):
    """Open a TOML file

    This is an intentionally minimal, loader-only approach that hands off
    to VisiData's Python object handling. Some non-obvious decisions:

    - Don't bother with incremental loading. Loading a TOML file returns
      a single dict. These files also tend to be small. So we load the
      sheet in one shot.

    - `PyobjSheet` is a higher-level VisiData sheet that delegates to
      child sheet types depending on the source's data type. VisiData's
      default handling of dicts uses "key" and "value" column names.
      If we wrap it in a list, the resulting sheet creates columns based
      on the dict keys. That seems a better fit for TOML.
    """
    return PyobjSheet(p.name, source=[tomllib.loads(p.read_text())])


vd.addGlobals(vd.getGlobals())
