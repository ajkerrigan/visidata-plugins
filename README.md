# VisiData Plugins

Custom plugins for https://github.com/saulpw/visidata/

## vds3: Open Amazon S3 paths and objects

### Installation

#### Install VisiData

This plugin is designed to work with the plugin framework coming with the [2.x](http://visidata.org/v2.x/) release.

Due to some recent upstream changes, I recommend installing from the `develop` branch:

```
pip3 install git+git://github.com/saulpw/visidata@develop
```

Once we see a stable VisiData 2.x release, the simpler `pip3 install visidata` should be sufficient.

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

2. Copy `vds3.py` to a `plugins` location inside your VisiData directory (by default, `~/.visidata`):

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

Because this plugin builds on top of s3fs and boto3, it takes advantage of standard AWS CLI configuration settings.

Be sure that the AWS CLI is [installed](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) to point to your desired AWS account.

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

`Enter`: Opens the current file or directory as a new sheet.  
`g+Enter`: Open all selected files and directories.

`q`'s behavior is unchanged (closes the current sheet), but while browsing a bucket it effectively becomes the "go up one level" command.

#### Browse all CSV files in a bucket (glob matching)

```
vd 's3://my-bucket/**/*.csv.gz
```

Since glob-matching can return results from multiple "directories" (S3 prefixes), the glob results sheet will display full object names rather than imitating a navigable directory hierarchy.

### Configuration

This plugin's behavior can be tweaked with the following options:

`vds3_glob` (Default: `True`): Enable glob matching for S3 paths. Glob-matching will only kick in for path names which contain glob patterns (`*`, `?`, `[` or `]`). However, it's possible to have S3 keys which *contain* those characters. In those cases, set this to `False` to explicitly disable glob-matching.

`vds3_endpoint` (Default: `None`): Specify a custom S3 endpoint. This can be useful for local testing, or for pairing this plugin with S3-compatible endpoints such as MinIO, Backblaze B2, etc.

Options can be configured directly in a `~/.visidatarc` file:

```python
options.vds3_glob = False
```

VisiData also supports changing options at runtime at a global level or per-sheet. Jeremy Singer-Vine's [tutorial](https://jsvine.github.io/intro-to-visidata/advanced/configuring-visidata/) is a helpful reference.

### Status

This plugin is in a "minimally viable" state - focused on basic S3 read operations. Reading directly from S3 into pandas/dask dataframes is not currently supported, nor is _writing_ to S3.

## kvpairs: Toggle values between lists of Key/Value pairs and dicts

### Overview

This plugin adds a pair of column-level convenience functions (`from_entries` and `to_entries`), which are similar to their [jq counterparts](https://stedolan.github.io/jq/manual/#to_entries,from_entries,with_entries). As of this writing, they're most useful for helping to break out tags from AWS API responses. For that specific case, this custom keybinding is a handy shortcut that composes with VisiData's existing "expand column" logic:

```python
Sheet.addCommand(
    "gz(",
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

And VisiData's `expand_cols_deep()` function (bound by default to `(`) breaks that into `Tags.Environment` and `Tags.Name` columns, so each tag becomes a first-class VisiData column.

### Installation

The `kvpairs` plugin is not currently included in VisiData's plugin framework. It can be installed manually by copying [kvpairs.py](plugins/kvpairs.py) to your local `~/.visidata/plugins` directory and including `import plugins.kvpairs` in your `~/.visidatarc` file.

## Contributing

Please open an issue for any bugs, questions or feature requests. Pull requests welcome!

## Acknowledgements

* VisiData is a slick tool - @saulpw and contributors have done a great job with it.
* @jsvine's [intro tutorial](https://jsvine.github.io/intro-to-visidata/) and [plugins repo](https://github.com/jsvine/visidata-plugins) are excellent references.
* Dask's [s3fs](https://github.com/dask/s3fs/) is a great foundation when you need to squint and pretend S3 is a filesystem.
