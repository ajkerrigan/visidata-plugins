import os
import subprocess
from shutil import which

from visidata import BaseSheet, Column, SuspendCurses, vd


@Column.api
def pageValue(col, row):
    pager = os.environ.get('PAGER', which('less'))
    with SuspendCurses():
        return subprocess.run(pager, input=str(col.getValue(row)), encoding='utf8')


BaseSheet.addCommand(
    "z^O", "syspager-cell", "cursorCol.pageValue(cursorRow)"
)
