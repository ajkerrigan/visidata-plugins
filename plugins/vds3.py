from textwrap import dedent

raise DeprecationWarning(
    dedent(
        """
        This plugin has been superseded by VisiData's native S3 loader.
        See also: https://github.com/saulpw/visidata/tree/develop/visidata/loaders
        """
    )
)
