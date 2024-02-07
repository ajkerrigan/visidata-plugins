"""
Launch an embedded ptipython REPL from within VisiData.
"""

from pathlib import Path

from ptpython.ipython import InteractiveShellEmbed, embed
from visidata import LazyChainMap, Sheet, SuspendCurses, VisiData


class Dummy:
    """Hacks to patch sheet-local variables that we want the REPL to ignore."""

    replayStatus = "dummy"
    someSelectedRows = "dummy"
    onlySelectedRows = "dummy"


@VisiData.api
def openRepl(vd):
    """Open a ptipython-based REPL that inherits VisiData's context."""

    def configure(python_input):
        python_input.title = "VisiData IPython REPL (ptipython)"

    with SuspendCurses():
        try:
            history_file = (
                Path(vd.options.visidata_dir).expanduser()
                / "cache"
                / "ptpython"
                / "history"
            )
            Path.mkdir(history_file.parent, parents=True, exist_ok=True)
            locals().update(dict(LazyChainMap(Dummy(), vd.sheet, locals=vd.getGlobals())))
            shell = InteractiveShellEmbed.instance(
                history_filename=str(history_file),
                vi_mode=True,
                configure=configure,
            )
            embed()
        except Exception as e:
            vd.exceptionCaught(e)
        finally:
            # The embedded IPython session is a singleton by default,
            # but launching it via `open-repl` in VisiData a second time
            # seems to either freeze or leave an exit message up from the
            # previous instance. Clean out the existing instance so any
            # future invocations get a fresh start.
            InteractiveShellEmbed.clear_instance()


Sheet.addCommand("", "open-repl", "vd.openRepl()")
