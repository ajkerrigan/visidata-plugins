import os
import subprocess
from shutil import which

from visidata import BaseSheet, Column, vd


@Column.api
def pageValue(col, row):
    pager = os.environ.get('PAGER', which('less'))
    subprocess.run(pager, input=str(col.getValue(row)), encoding='utf8')
    vd.redraw()


BaseSheet.addCommand(
    "z^O", "syspager-cell", "cursorCol.pageValue(cursorRow)"
)
