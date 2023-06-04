"""
Experimental / proof of concept VisiData remote control functionality
implemented as a plugin with a dedicated remote control sheet type.

To try it, open a sheet with:

vd server://remote_control

And try controlling it from another tab/window by sending requests to
the socket:

echo "vd.status('hello from elsewhere!')" | nc -Uuq 0 ~/.visidata/run/remote_control

Warnings/Limitations:

- Don't expect too much
- Only tested on Linux (a more portable approach would probably be
  adapting this to use a UDP server instead)
- ...but I explicitly didn't want to use a network server for this
  sample. I mean, we're already opening VisiData up to arbitrary
  remote control with no auth/validation/etc. That's enough sin in
  one place
"""

import socketserver
from contextlib import suppress
from pathlib import Path

from visidata import ItemColumn, Sheet, asyncthread, vd
from visidata.settings import Command


class RemoteControlCommand(Command):
    def __init__(self, execstr):
        super().__init__("remote-control", execstr)


class VisiDataRemoteControlHandler(socketserver.BaseRequestHandler):
    """Handle socket requests as VisiData exec strings

    Log commands as rows in a remote control sheet, including any
    errors.
    """

    def handle(self):
        data = self.request[0].strip().decode("utf8")
        error = None
        try:
            self.server.sheet.execCommand2(RemoteControlCommand(data))
        except Exception as err:
            error = err
        self.server.sheet.addRow(dict(command=data, error=error))


class RemoteControlSheet(Sheet):
    """A sheet that provides rudimentary remote control features

    On startup, set up a Unix socket under ~/.visidata/run where the
    filename is based on the path, so:

    vd server://moo

    opens a Unix domain socket at ~/.visidata/run/moo. Clients can
    send VisiData exec strings to that socket, for example:

    echo "vd.status('hello from elsewhere!')" | nc -Uuq 0 ~/.visidata/run/moo

    Shut down the socket and remove the file when the sheet closes.
    """

    columns = [ItemColumn("command"), ItemColumn("error")]

    def __init__(self, name):
        super().__init__(name)
        Path("~/.visidata/run").expanduser().mkdir(parents=True, exist_ok=True)
        self.server = socketserver.UnixDatagramServer(
            str(Path(f"~/.visidata/run/{name}").expanduser()),
            VisiDataRemoteControlHandler,
        )
        self.server.sheet = self
        self.serve()

    @asyncthread
    def serve(self):
        self.server.serve_forever()
        vd.status("server closed")


@RemoteControlSheet.api
def confirmQuit(vs, verb="quit"):
    """Try to avoid leaving dangling socket nonsense"""

    super(vs.__class__, vs).confirmQuit(verb)
    vd.status("closing server")
    vs.server.shutdown()
    with suppress(OSError, FileNotFoundError):
        sockname = vs.server.socket.getsockname()
        vd.status(f"removing file {sockname}")
        Path(sockname).expanduser().unlink()


def openurl_server(p, filetype):
    return RemoteControlSheet(p.name)


vd.addGlobals({"openurl_server": openurl_server})
