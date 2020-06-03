import os
import subprocess
from shutil import which

from visidata import BaseSheet, vd


def page(col, row):
    pager = os.environ.get('PAGER', which('less'))
    subprocess.run(pager, input=str(col.getValue(row)), encoding='utf8')
    vd.redraw()


BaseSheet.addCommand(
    "z^O", "syspager-cell", "plugins.vpager.page(cursorCol, cursorRow)"
)
