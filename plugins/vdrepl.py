'''
Launch an embedded ptipython REPL from within VisiData.
'''

import sys

from pathlib import Path

from ptpython.ipython import embed, InteractiveShellEmbed
from prompt_toolkit.history import ThreadedHistory, FileHistory
from visidata import LazyChainMap, Sheet, SuspendCurses, VisiData, vd


class Dummy:
    '''Hacks to patch sheet-local variables that we want the REPL to ignore.'''

    replayStatus = 'dummy'
    someSelectedRows = 'dummy'


@VisiData.api
def openRepl(self):
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    try:
        # Provide local top-level access to VisiData global and sheet-local
        # variables, similar to VisiData's `execCommand` context.
        new_locals = LazyChainMap(Dummy(), vd, vd.sheet)
        locals().update(new_locals)
    except Exception as e:
        vd.exceptionCaught(e)

    with SuspendCurses():
        try:
            sys.stdin = vd._stdin
            sys.stdout = open('/dev/tty', mode='w')
            history_file = (
                Path(vd.options.visidata_dir).expanduser()
                / 'cache'
                / 'ptpython'
                / 'history'
            )
            Path.mkdir(history_file.parent, parents=True, exist_ok=True)
            shell = InteractiveShellEmbed.instance(
                history_filename=str(history_file), vi_mode=True,
            )
            shell.python_input.title = 'VisiData IPython REPL (ptipython)'
            shell.python_input.show_exit_confirmation = False
            embed()
        except Exception as e:
            vd.exceptionCaught(e)
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout

Sheet.addCommand("gz^X", "open-repl", "vd.openRepl()")
