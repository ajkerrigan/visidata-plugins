# vds3: Open Amazon S3 paths and objects

## Demo

Browse S3 with an interface like a console-based file explorer:

[![asciicast](https://asciinema.org/a/Cw1njUzYDHvkRrjoKAykYHKe4.svg)](https://asciinema.org/a/Cw1njUzYDHvkRrjoKAykYHKe4)

Use glob-matching to focus your search:

[![asciicast](https://asciinema.org/a/yjPEjpDa5p45dCe7Sad8NYEQd.svg)](https://asciinema.org/a/yjPEjpDa5p45dCe7Sad8NYEQd)

## Installation

### Install VisiData

Via pip:

```
pip3 install visidata
```

There is a comprehensive guide to various installation methods
[here](https://www.visidata.org/install/). I prefer using
[pipx](https://github.com/pipxproject/pipx) for the main install, and `pipx inject` to add plugin
dependencies. Choose whichever install method works best for you, as long as you install VisiData
2.0 or higher.

### Install the Plugin

This plugin can be installed using VisiData's built-in plugin framework, or manually.

#### Using the Plugin Framework (Recommended)

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

#### Using pip (experimental)

1. Run `python3 -m pip install visidata-s3` in your VisiData Python environment
2. Add the following line to your `~/.visidatarc` file:

```python
import visidata_s3
```

#### Manually

1. Install [s3fs](https://s3fs.readthedocs.io):

```
pip3 install s3fs
```

2. Copy `vds3.py` to a `plugins` subdirectory inside your VisiData directory (by default,
   `~/.visidata`):

```
mkdir -p ~/.visidata/plugins
cd path/to/visidata-plugins
cp visidata_s3/visidata_s3/vds3.py ~/.visidata/plugins
```

3. Add this line to your `~/.visidatarc` file:

```python
import plugins.vds3
```

## Usage

Because this plugin builds on top of s3fs and boto3, it takes advantage of standard AWS CLI
configuration settings.

Be sure that the AWS CLI is
[installed](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) and
[configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) to point to
your desired AWS account.

### Open a file stored in S3

```
vd 's3://my-bucket/path/to/file.json.gz'
```

### List all buckets

```
vd 's3://'
```

### Browse a bucket's contents

```
vd 's3://my-bucket'
vd 's3://my-bucket/path'
```

When browsing a bucket, VisiData will behave like a file explorer:

`Enter`: Opens the current file or directory as a new sheet. `g+Enter`: Open all selected files and
directories.

`q`'s behavior is unchanged (closes the current sheet), but while browsing a bucket it effectively
becomes the "go up one level" command.

### Browse all CSV files in a bucket (glob matching)

```
vd 's3://my-bucket/**/*.csv.gz
```

Since glob-matching can return results from multiple "directories" (S3 prefixes), the glob results
sheet will display full object names rather than imitating a navigable directory hierarchy.

### Browse previous versions of objects

Open an S3 path:

```
vd 's3://my-bucket'
vd 's3://my-bucket/path'
```

Hit `^V` to toggle support for S3 versioning. When enabled, there will be an additional `Latest?`
column along with a `Version ID` column that is hidden by default. Previous versions can be opened
with `Enter` or `g+Enter` as usual.

### Join/combine objects

From an S3 directory listings, select multiple objects and use `&` to join object contents into a
single sheet. This uses the native VisiData join functionality under the hood, so the available join
types match those described in VisiData's [join documentation](https://www.visidata.org/docs/join/).

## Configuration

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

## Status

This plugin is in a "minimally viable" state - focused on basic S3 read operations. Reading directly
from S3 into pandas/dask dataframes is not currently supported, nor is _writing_ to S3.
