'''
Launch an embedded ptipython REPL from within VisiData.
'''

import sys

from ptpython.ipython import embed, InteractiveShellEmbed
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
            shell = InteractiveShellEmbed.instance()
            shell.python_input.show_exit_confirmation = False
            shell.python_input.vi_mode = True
            embed()
            shell.reset()
        except Exception as e:
            vd.exceptionCaught(e)
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout

Sheet.addCommand(
    "gz^X", "open-repl", "vd.openRepl()"
)
