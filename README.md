# VisiData Plugins

![](https://github.com/ajkerrigan/visidata-plugins/workflows/CI%20Tests/badge.svg)

Custom plugins for https://github.com/saulpw/visidata/

* [vds3](visidata_s3/README.md): Open Amazon S3 paths and objects
* [kvpairs](#kvpairs-toggle-values-between-lists-of-keyvalue-pairs-and-dicts): Toggle between
  key/value pairs and dicts
* [vfake_extensions](#vfake_extensions-niche-addons-for-vfake): Niche addons for
  [vfake](https://github.com/saulpw/visidata/blob/develop/plugins/vfake.py)
* [vpager](#vpager-open-long-cell-values-in-the-system-pager): Open long cell values in the system
  pager
* [debugging_helpers](#debugging_helpers-integrate-visidata-with-debugging-packages): Integrate
  VisiData with debugging packages
* [split_navigation](#split_navigation-navigation-keybindings-for-masterdetail-split-views):
  Navigation keybindings for master/detail split views
* [vd_jmespath](#vd_jmespath-evaluate-jmespath-expressions): Use JMESPath expressions to add columns
  or toggle row selection

## kvpairs: Toggle values between lists of Key/Value pairs and dicts

### Overview

This plugin adds a pair of column-level convenience functions (`from_entries` and `to_entries`),
which are similar to their [jq
counterparts](https://stedolan.github.io/jq/manual/#to_entries,from_entries,with_entries). As of
this writing, they're most useful for helping to break out tags from AWS API responses. For that
specific case, this custom keybinding is a handy shortcut that composes with VisiData's existing
"expand column" logic:

```python
Sheet.addCommand(
    "gz{",
    "expand-tags",
    "expand_cols_deep(sheet, [sheet.colsByName['Tags'].from_entries()], cursorRow)"
)
```

In that scenario, assume we have a `Tags` column whose data looks like this:

```json
[
    {"Key": "Environment", "Value": "production"},
    {"Key": "Name", "Value": "my-project"}
]
```

`from_entries()` turns that into this:

```json
{
    "Environment": "production",
    "Name": "my-project"
}
```

And VisiData's `expand_cols_deep()` function (bound by default to `(`) breaks that into
`Tags.Environment` and `Tags.Name` columns, so each tag becomes a first-class VisiData column.

### Installation

The `kvpairs` plugin is not currently included in VisiData's plugin framework. It can be installed
manually by copying [kvpairs.py](plugins/kvpairs.py) to your local `~/.visidata/plugins` directory
and including `import plugins.kvpairs` in your `~/.visidatarc` file.

## vfake_extensions: Niche addons for vfake

### Overview

VisiData's [vfake](https://github.com/saulpw/visidata/blob/develop/plugins/vfake.py) plugin provides
interactive access to some common [Faker](faker.readthedocs.io/) functionality. The extra bits in
vfake_extensions are some personal customizations. They skew heavily toward AWS and are probably
most useful as a reference/inspiration for other vfake customizations.

### Installation

This plugin won't be included in VisiData, and probably shouldn't be added manually as-is either. If
you find any pieces of [vfake_extensions.py](plugins/vfake_extensions.py) useful, transplant them
into your own `~/.visidatarc` file or personal plugin collection inside `~/.visidata/plugins`.

### Usage

`VdCustomProvider` could be a helpful reference if you have a need to define your own custom Faker
generator functions for use with vfake.

The `autofake` functionality can save a lot of time if you repeatedly generate fake data for values
that follow predictable patterns.

### Autofake Demo

[![asciicast](https://asciinema.org/a/MXZCY6yT6AEduQhuCYQlWGHHH.svg)](https://asciinema.org/a/MXZCY6yT6AEduQhuCYQlWGHHH)

## vpager: Open long cell values in the system pager

### Overview

For cells that contain long strings, it can sometimes be easier to pass the value into an external
viewer rather than relying on VisiData's line wrapping. This plugin supports arbitrary external
commands. Unless otherwise specified it relies on the `PAGER` environment variable, and defaults to
`less`.

### Installation

* Option 1: Include the contents of [vpager.py](plugins/vpager.py) in your `~/.visidatarc` file.
* Option 2:
  * Copy [vpager.py](plugins/vpager.py) to your local `~/.visidata/plugins` directory.
  * Add `import plugins.vpager` to `~/.visidata/plugins/__init__.py`
  * Add `import plugins` to `~/.visidatarc` if it is not there already

* Define keybindings or options in your `~/.visidatarc` file. Examples:

```python
from visidata import BaseSheet, vd

# Use spacebar as a custom command prefix, and shuffle other bindings
# around to accommodate that.
BaseSheet.unbindkey(' ')
vd.allPrefixes.append(' ')
vd.bindkeys[':'] = {'BaseSheet': 'exec-longname'}
BaseSheet.bindkey(' ;', 'split-col')

# Tell `open-cell-pager` to invoke `bat` rather than $PAGER
vd.options.vpager_cmd = '/usr/bin/env bat --paging=always'

# Space+Enter: Open a cell's values with the default viewer - `vpager_cmd`
#              if it's defined, otherwise $PAGER.
#
# Space+m: Open a cell's value in `glow` for prettier rendered markdown
#          in the terminal.
BaseSheet.bindkey(" Enter", "open-cell-pager")
BaseSheet.addCommand(" m", "open-cell-markdown", "cursorCol.pageValue(cursorRow, cmd='glow -p')")
```

### Usage

Navigate to a cell with a long value, and use the `View` --> `Open cell with` menu to open that cell
with an external program.

If you've defined custom keys for the `open-cell-*` group of commands, use those instead of menus.

## debugging_helpers: Integrate VisiData with debugging packages

### Overview

VisiData is a multi-threaded curses application, which can trip up some traditional console-based
debugging tools. For example, vanilla pdb is a terrible fit for VisiData - the output is all over
the place.

This plugin adds a `--debugger` option, initially supporting the following debuggers:

* [PuDB](https://github.com/inducer/pudb)
* [remote-pdb](https://github.com/ionelmc/python-remote-pdb/)
* [web-pdb](https://pypi.org/project/web-pdb/)

Since the latter two wrap [pdb](https://docs.python.org/3/library/pdb.html), they will automatically
use [pdb++](https://github.com/pdbpp/pdbpp) if it's installed.

### Workflow

Install a supported debugger via pip, then run VisiData with the `--debugger` option:

```bash
vd --debugger pudb sample_data/benchmark.csv
```

VisiData should immediately trigger a breakpoint. The behavior here varies by debugger:

* PuDB: Takes over your screen immediately
* remote-pdb: Awaits a connection (`telnet 127.0.0.1 4444` or `nc 127.0.0.1 4444` from another
  pane/window)
* web-pdb: Awaits a web connection (browse to http://localhost:5555)

Once the debugger is active, you can start poking around right away or continue execution with `c`.
At that point, the debugger will set up an event handler for the interrupt signal. This plugin binds
`z^C` (`z, Ctrl-C`) as an interrupt keybinding, so that becomes your interactive "break on demand"
shortcut.

### Notes

* I had issues with several of PuDB's shell options (ptpython, ptipython, bpython). I had more
  success setting up a [modified bpython shell](extras/pudb_bpython_shell.py) as a PuDB [custom
  shell](https://documen.tician.de/pudb/shells.html#custom-shells).
* PuDB works great as a full-screen debugger, but [debugging from a separate
  terminal](https://documen.tician.de/pudb/starting.html#debugging-from-a-separate-terminal) is also
  handy if you need to see the debugger without hiding the VisiData screen. VisiData and PuDB in
  separate panes of the same tmux window is a nice setup.
* Even with some careful debugger choices and configuration, VisiData and the debugger can sometimes
  draw over each other. When that happens, VisiData's `^L` binding to redraw the screen is helpful.
* Despite all the links and notes here, I mostly debug with the [VS Code Python
  extension](https://code.visualstudio.com/docs/languages/python#_debugging) which makes this plugin
  completely useless! 😃

### Demo

[![asciicast](https://asciinema.org/a/jFKTO1PNyHrqtecJcvYiFQQWh.svg)](https://asciinema.org/a/jFKTO1PNyHrqtecJcvYiFQQWh)

## split_navigation: Navigation keybindings for master/detail split views

### Overview

VisiData's [split window](https://www.visidata.org/blog/2020/splitwin/) feature enables interesting
use cases like displaying a data set and frequency table simultaneously, or a master list of records
and a child view of details. In that second case, it can be useful to keep focus in the child/detail
view while navigating up and down in the parent view. This little plugin sets up keybindings for
that.

### Demos

#### Master/Detail Split Navigation

[![asciicast](https://asciinema.org/a/C18e5aAOwKXTAr4njekNQXWLt.svg)](https://asciinema.org/a/C18e5aAOwKXTAr4njekNQXWLt)

#### Frequency Table "Zoom" Navigation

[![asciicast](https://asciinema.org/a/hS2cSpo7rHI2FN0piscFSlRm5.svg)](https://asciinema.org/a/hS2cSpo7rHI2FN0piscFSlRm5)

## vd_jmespath: Evaluate JMESPath expressions

### Overview

[JMESPath](https://jmespath.org/) is a query language for JSON data. This plugin adds VisiData
commands to add columns or select rows based on JMESPath expressions.

### Installation

* Option 1: Include the contents of [vd_jmespath.py](plugins/vd_jmespath.py) in your `~/.visidatarc`
  file.
* Option 2:
  * Copy [vd_jmespath.py](plugins/vd_jmespath.py) to your local `~/.visidata/plugins` directory.
  * Add `import plugins.vd_jmespath` to `~/.visidata/plugins/__init__.py`
  * Add `import plugins` to `~/.visidatarc` if it is not there already

This plugin adds commands but does _not_ define its own keyboard shortcuts for them, since those are
a matter of personal preference and the risk of collisions is high. Instead, you can define your own
shortcuts in `~/.visidatarc`. For reference, mine look like this:

```python
from visidata import BaseSheet, vd

# Use space as a prefix key rather than to execute a command by name.
vd.bindkeys[':'] = {'BaseSheet': 'exec-longname'}
vd.allPrefixes.append(' ')

# Define JMESPath commands by adding a custom prefix to the built-in
# addcol/select/unselect commands.
BaseSheet.bindkey(' =', 'addcol-jmespath')
BaseSheet.bindkey(' |', 'select-jmespath')
BaseSheet.bindkey(' \\', 'unselect-jmespath')
```

### Usage

Inside a sheet containing JSON data:

* `addcol-jmespath` adds a new column by evaluating a given expression against each row
* `select-jmespath` and `unselect-jmespath` toggle row selection based on an expression

## Contributing

Please open an issue for any bugs, questions or feature requests. Pull requests welcome!

## Acknowledgements

* VisiData is a slick tool - [saulpw](https://github.com/saulpw),
  [anjakefala](https://github.com/anjakefala) and other contributors have done a great job with it.
* [jsvine](https://github.com/jsvine)'s [intro
  tutorial](https://jsvine.github.io/intro-to-visidata/) and [plugins
  repo](https://github.com/jsvine/visidata-plugins) are excellent references.
* Dask's [s3fs](https://github.com/dask/s3fs/) is a great foundation when you need to squint and
  pretend S3 is a filesystem.
* Thanks to [geekscrapy](https://github.com/geekscrapy) and
  [frosencrantz](https://github.com/frosencrantz) for testing and helping to improve these plugins.
