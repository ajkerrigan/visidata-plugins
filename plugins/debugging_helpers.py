import os
import signal
from functools import wraps

from visidata import BaseSheet, options, vd

vd.option('debugger', '', 'Activate the specified debugger')

SUPPORTED_DEBUGGERS = [
    'remote-pdb',  # dependency: remote-pdb, nice to have: pdbpp
    'pudb',  # dependency: pudb, nice to have: bpython
    'web-pdb',  # dependency: web-pdb, nice to have but ugly by default: pdbpp
]


def setup_debugger():
    '''
    Rig up breakpoint() behavior based on the debugger option. Return True
    if we set up a debugger, False otherwise.
    '''

    if options.debugger not in SUPPORTED_DEBUGGERS:
        vd.status(f'Skipping setup for unknown debugger: {options.debugger}')
        return False

    debugger_env = {
        'remote-pdb': {
            'PYTHONBREAKPOINT': 'remote_pdb.set_trace',
            'REMOTE_PDB_HOST': '127.0.0.1',
            'REMOTE_PDB_PORT': '4444',
        },
        'pudb': {'PYTHONBREAKPOINT': 'pudb.set_trace',},
        'web-pdb': {'PYTHONBREAKPOINT': 'web_pdb.set_trace',},
    }

    os.environ.update(debugger_env[options.debugger])
    return True


def break_once(obj, func):
    '''
    Wrap obj.func() to perform initial debugger setup and trigger a breakpoint.
    After one invocation, restore the original function.
    '''

    f = getattr(obj, func)

    @wraps(f)
    def wrapper(*args, **kwargs):
        setup_debugger() and breakpoint() or vd.status('Skipping debugger setup')
        f(*args, **kwargs)
        setattr(obj, func, f)
        vd.status(f'{func} function restored to original')

    setattr(obj, func, wrapper)
    vd.status(f'{func} function wrapped to initialize debugging')


# Hijack the first invocation of vd.push to get the debugger active
# early, without having to touch the source.
break_once(vd, 'push')


def interrupt():
    os.kill(os.getpid(), signal.SIGINT)


# Interrupt execution and return control to the active debugger.
# ^C is traditional, but it's already used in VisiData for cancelling
# async threads.
BaseSheet.addCommand('z^C', 'debug-break', f'{__name__}.interrupt()')
