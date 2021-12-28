import os
import shlex
import subprocess
from shutil import which

from visidata import BaseSheet, Column, SuspendCurses, vd

vd.option("vpager_cmd", "", "default external command for displaying cell contents")


@Column.api
def pageValue(col, row, cmd=None):
    pager = cmd or vd.options.vpager_cmd or os.environ.get("PAGER", which("less"))
    with SuspendCurses():
        return subprocess.run(
            shlex.split(pager), input=str(col.getValue(row)), encoding="utf8"
        )


@Column.api
def pageValueWith(col, row):
    pager = vd.input("external command: ", type="pager")
    col.pageValue(row, pager)


BaseSheet.addCommand(
    "",
    "open-cell-pager",
    "cursorCol.pageValue(cursorRow)",
    "view a cell using the default pager",
)
BaseSheet.addCommand(
    "",
    "open-cell-with",
    "cursorCol.pageValueWith(cursorRow)",
    "view a cell using an external program",
)

try:
    vd.addMenuItem("View", "Open cell with", "configured pager", "open-cell-pager")
    vd.addMenuItem("View", "Open cell with", "custom pager...", "open-cell-with")
except AttributeError:
    vd.debug("menu support not detected, skipping menu item setup")
