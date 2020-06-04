import bpython  # noqa

# A curtsies adaptation of the bpython curses-based shell in:
#
# https://github.com/inducer/pudb/blob/cd10e5a/pudb/shell.py

# {{{ combined locals/globals dict

class SetPropagatingDict(dict):
    """
    Combine dict into one, with assignments affecting a target dict
    The source dicts are combined so that early dicts in the list have higher
    precedence.
    Typical usage is ``SetPropagatingDict([locals, globals], locals)``. This
    is used for functions like ``rlcompleter.Completer`` and
    ``code.InteractiveConsole``, which only take a single dictionary. This
    way, changes made to it are propagated to locals. Note that assigning to
    locals only actually works at the module level, when ``locals()`` is the
    same as ``globals()``, so propagation doesn't happen at all if the
    debugger is inside a function frame.
    """
    def __init__(self, source_dicts, target_dict):
        dict.__init__(self)
        for s in source_dicts[::-1]:
            self.update(s)

        self.target_dict = target_dict

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.target_dict[key] = value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        del self.target_dict[key]

# }}}

def pudb_shell(globals, locals):
    ns = SetPropagatingDict([locals, globals], locals)

    import bpython.curtsies
    bpython.curtsies.main(args=[], locals_=ns)
