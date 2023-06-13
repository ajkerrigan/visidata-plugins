# VisiData Plugins

![](https://github.com/ajkerrigan/visidata-plugins/workflows/CI%20Tests/badge.svg)

Custom plugins for https://github.com/saulpw/visidata/

- [vds3: Open Amazon S3 paths and objects](#vds3-open-amazon-s3-paths-and-objects)
  - [Demo](#demo)
  - [Installation](#installation)
    - [Install VisiData](#install-visidata)
    - [Install the Plugin](#install-the-plugin)
      - [Using the Plugin Framework (Recommended)](#using-the-plugin-framework-recommended)
      - [Manually](#manually)
  - [Usage](#usage)
    - [Open a file stored in S3](#open-a-file-stored-in-s3)
    - [List all buckets](#list-all-buckets)
    - [Browse a bucket's contents](#browse-a-buckets-contents)
    - [Browse all CSV files in a bucket (glob matching)](#browse-all-csv-files-in-a-bucket-glob-matching)
    - [Browse previous versions of objects](#browse-previous-versions-of-objects)
    - [Join/combine objects](#joincombine-objects)
  - [Configuration](#configuration)
  - [Status](#status)
- [kvpairs: Toggle values between lists of Key/Value pairs and dicts](#kvpairs-toggle-values-between-lists-of-keyvalue-pairs-and-dicts)
  - [Overview](#overview)
  - [Installation](#installation-1)
- [vfake\_extensions: Niche addons for vfake](#vfake_extensions-niche-addons-for-vfake)
  - [Overview](#overview-1)
  - [Installation](#installation-2)
  - [Usage](#usage-1)
  - [Autofake Demo](#autofake-demo)
- [vpager: Open long cell values in the system pager](#vpager-open-long-cell-values-in-the-system-pager)
  - [Overview](#overview-2)
  - [Installation](#installation-3)
  - [Usage](#usage-2)
- [debugging\_helpers: Integrate VisiData with debugging packages](#debugging_helpers-integrate-visidata-with-debugging-packages)
  - [Overview](#overview-3)
  - [Workflow](#workflow)
  - [Notes](#notes)
  - [Demo](#demo-1)
- [parent\_navigation: Helpers for navigating a parent sheet from its child](#parent_navigation-helpers-for-navigating-a-parent-sheet-from-its-child)
  - [Overview](#overview-4)
  - [Installation](#installation-4)
  - [Usage](#usage-3)
  - [Demos](#demos)
    - [Parent/Child Sheet Navigation](#parentchild-sheet-navigation)
    - [Frequency Table "Zoom" Navigation](#frequency-table-zoom-navigation)
- [vd\_jmespath: Evaluate JMESPath expressions](#vd_jmespath-evaluate-jmespath-expressions)
  - [Overview](#overview-5)
  - [Installation](#installation-5)
  - [Usage](#usage-4)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
## vds3: Open Amazon S3 paths and objects

### Demo

**Note:** This plugin's functionality has been migrated into VisiData core. If you're using VisiData v2.12dev or higher,
you no longer need this plugin!

Browse S3 with an interface like a console-based file explorer:

[![asciicast](https://asciinema.org/a/Cw1njUzYDHvkRrjoKAykYHKe4.svg)](https://asciinema.org/a/Cw1njUzYDHvkRrjoKAykYHKe4)

Use glob-matching to focus your search:

[![asciicast](https://asciinema.org/a/yjPEjpDa5p45dCe7Sad8NYEQd.svg)](https://asciinema.org/a/yjPEjpDa5p45dCe7Sad8NYEQd)

### Installation

#### Install VisiData

Via pip:

```
pip3 install visidata
```

There is a comprehensive guide to various installation methods
[here](https://www.visidata.org/install/). I prefer using
[pipx](https://github.com/pipxproject/pipx) for the main install, and `pipx inject` to add plugin
dependencies. Choose whichever install method works best for you, as long as you install VisiData
2.0 or higher.

#### Install the Plugin

This plugin can be installed using VisiData's built-in plugin framework, or manually.

##### Using the Plugin Framework (Recommended)

1. Start VisiData.

```
vd
```

2. Hit `<Space>`, type `open-plugins` and hit `<Enter>` to open the plugins sheet.

3. Scroll to the `vds3` plugin and hit `a` to add it.

4. Wait for installation to complete, then exit VisiData.

5. Be sure that your `~/.visidatarc` file contains the line:

```python
import plugins
```

6. Restart VisiData.

##### Manually

1. Install [s3fs](https://s3fs.readthedocs.io):

```
pip3 install s3fs
```

2. Copy `vds3.py` to a `plugins` subdirectory inside your VisiData directory (by default,
   `~/.visidata`):

```
mkdir -p ~/.visidata/plugins
cd path/to/visidata-plugins
cp plugins/vds3.py ~/.visidata/plugins
```

3. Add this line to your `~/.visidatarc` file:

```python
import plugins.vds3
```

### Usage

Because this plugin builds on top of s3fs and boto3, it takes advantage of standard AWS CLI
configuration settings.

Be sure that the AWS CLI is
[installed](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) and
[configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) to point to
your desired AWS account.

#### Open a file stored in S3

```
vd 's3://my-bucket/path/to/file.json.gz'
```

#### List all buckets

```
vd 's3://'
```

#### Browse a bucket's contents

```
vd 's3://my-bucket'
vd 's3://my-bucket/path'
```

When browsing a bucket, VisiData will behave like a file explorer:

`Enter`: Opens the current file or directory as a new sheet. `g+Enter`: Open all selected files and
directories.

`q`'s behavior is unchanged (closes the current sheet), but while browsing a bucket it effectively
becomes the "go up one level" command.

#### Browse all CSV files in a bucket (glob matching)

```
vd 's3://my-bucket/**/*.csv.gz
```

Since glob-matching can return results from multiple "directories" (S3 prefixes), the glob results
sheet will display full object names rather than imitating a navigable directory hierarchy.

#### Browse previous versions of objects

Open an S3 path:

```
vd 's3://my-bucket'
vd 's3://my-bucket/path'
```

Hit `^V` to toggle support for S3 versioning. When enabled, there will be an additional `Latest?`
column along with a `Version ID` column that is hidden by default. Previous versions can be opened
with `Enter` or `g+Enter` as usual.

#### Join/combine objects

From an S3 directory listings, select multiple objects and use `&` to join object contents into a
single sheet. This uses the native VisiData join functionality under the hood, so the available join
types match those described in VisiData's [join documentation](https://www.visidata.org/docs/join/).

### Configuration

This plugin's behavior can be tweaked with the following options:

`vds3_glob` (Default: `True`): Enable glob matching for S3 paths. Glob-matching will only kick in
for path names which contain glob patterns (`*`, `?`, `[` or `]`). However, it's possible to have S3
keys which *contain* those characters. In those cases, set this to `False` to explicitly disable
glob-matching.

`vds3_endpoint` (Default: `None`): Specify a custom S3 endpoint. This can be useful for local
testing, or for pairing this plugin with S3-compatible endpoints such as MinIO, Backblaze B2, etc.

**Note:** This sample `~/.visidatarc` snippet defines local S3 endpoints to be used when specific
AWS profiles are active. It assumes that if the `moto` or `localstack` AWS CLI profiles are active,
you have a local [moto server](https://github.com/spulec/moto#stand-alone-server-mode) or
[localstack](https://github.com/localstack/localstack) S3 service running on a specific port. For
any other AWS profile it falls back to the AWS default endpoint. A block like this can help you
naturally switch between endpoints based on context, rather than requiring command line switches.

```python
profile_endpoint_map = {
    'localstack': 'http://localhost:4572',
    'moto': 'http://localhost:3000',
}
options.vds3_endpoint = profile_endpoint_map.get(os.environ.get('AWS_PROFILE'))
```

Options can be configured directly in a `~/.visidatarc` file:

```python
options.vds3_glob = False
```

Or specified at runtime:

```bash
vd --vds3-glob false 's3://my-bucket/file[?].json'
```

VisiData also supports changing options from the Options sheet inside the application. Jeremy
Singer-Vine's [tutorial](https://jsvine.github.io/intro-to-visidata/advanced/configuring-visidata/)
is a helpful reference for that.

### Status

This plugin is in a "minimally viable" state - focused on basic S3 read operations. Reading directly
from S3 into pandas/dask dataframes is not currently supported, nor is _writing_ to S3.

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

<a name="split_navigation-navigation-keybindings-for-masterdetail-split-views"></a>

## parent_navigation: Helpers for navigating a parent sheet from its child

### Overview

VisiData's [split window](https://www.visidata.org/blog/2020/splitwin/) feature enables interesting
use cases like displaying a data set and frequency table simultaneously, or a master list of records
and a child view of details. In that second case, it can be useful to keep focus in the child/detail
view while navigating up and down in the parent view. This little plugin sets up keybindings for
that.

### Installation

1. Copy [parent_navigation.py](plugins/parent_navigation.py) to your local `~/.visidata/plugins` directory.
1. Add `import plugins.parent_navigation` to `~/.visidata/plugins/__init__.py`
1. Add `import plugins` to `~/.visidatarc` if it is not there already

This plugin adds commands but does _not_ define its own keyboard shortcuts for them, since those are
a matter of personal preference and the risk of collisions is high. Instead, you can define your own
shortcuts in `~/.visidatarc`. For reference, mine look like this:

```python
TableSheet.bindkey(ALT + "j", "next-parent-row")
TableSheet.bindkey(ALT + "k", "prev-parent-row")

FreqTableSheet.bindkey(ALT + "j", "zoom-next-freqrow")
FreqTableSheet.bindkey(ALT + "k", "zoom-prev-freqrow")
FreqTableSheet.bindkey(ALT + ENTER, "zoom-cur-freqrow")
```

So `j` and `k` move in the current sheet, but with `Alt` they move in a parent sheet instead.

### Usage

* With a sheet open in VisiData, dive into the details of a row (`Enter`) or cell (`z` + `Enter`)
* Use the `next-parent-row` and `prev-parent-row` commands to navigate a parent sheet, refreshing
  the child sheet as you go
  * **Note:** This pairs nicely with VisiData's support for [split views](https://www.visidata.org/docs/split/),
    which allow you to see the parent and child sheets at the same time.
### Demos

#### Parent/Child Sheet Navigation

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
vd.allPrefixes.append('Space')

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
