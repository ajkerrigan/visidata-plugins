import os
import shlex
import subprocess
from shutil import which

from visidata import BaseSheet, Column, SuspendCurses, vd

vd.option("vpager_cmd", "", "external command for displaying cell contents")


@Column.api
def pageValue(col, row, cmd=None):
    pager = cmd or vd.options.vpager_cmd or os.environ.get("PAGER", which("less"))
    with SuspendCurses():
        return subprocess.run(
            shlex.split(pager), input=str(col.getValue(row)), encoding="utf8"
        )

BaseSheet.addCommand("", "syspager-cell", "cursorCol.pageValue(cursorRow)")
