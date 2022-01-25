from functools import lru_cache

from visidata import FreqTableSheet, PyobjSheet, TableSheet, vd

__version__ = "0.1"

# A "child" sheet may come from diving into different entities of a parent sheet
CHILD_ENTITY_TYPES = ["cell", "row"]


@lru_cache
def _placeholderSheet(entityType):
    """
    An empty sheet to stand in when scrolling to a parent entity (row/cell)
    with no content. Create these once per entity type only when needed.
    """
    return PyobjSheet("placeholder", f"No content in parent {entityType}")


def _noContentStatus():
    """
    Does the most recent status entry show an attempt to open an
    empty sheet?
    """
    _, last_status_args, _ = vd.statusHistory[-1]
    return any(("no content" in arg for arg in last_status_args))


def _replaceDetailSheet(parentRowIdx, entityType):
    """
    Try to refresh a child window with data from a given parent
    entity (row or cell).
    """
    placeholder = _placeholderSheet(entityType)
    openCommand = f"open-{entityType}"

    if vd.sheet is placeholder or openCommand in (
        cmd.longname for cmd in vd.sheet.cmdlog_sheet.rows
    ):
        parent = vd.sheets[1]
        vd.remove(vd.sheet)
        parent.cursorRowIndex = parentRowIdx
        parent.execCommand(openCommand)
        if vd.sheet is parent and _noContentStatus():
            vd.push(placeholder)
        return vd.sheet


@TableSheet.api
def goParentRow(_, by):
    """
    While focused in a child "detail" sheet, navigate through rows
    in the parent sheet.
    """

    parent = vd.sheets[1]
    newIndex = parent.cursorRowIndex + by
    if newIndex < 0:
        vd.status("Already at the top!")
        return
    elif newIndex >= len(parent.rows):
        vd.status("Already at the bottom!")
        return

    # The goal here is to navigate around a parent window in a consistent way,
    # updating a child view in the process. Find out whether the current
    # sheet represents a detail view of the cursor _row_ or _cell_ in the
    # parent sheet. Use that to determine how to update the child view.
    #
    # Edge case:
    #
    # * When scrolling through parent cells that would yield no child content
    #   (and therefore not open a sheet), we need a dummy stand-in sheet to
    #   keep the child window open and avoid breaking things. This happens
    #   when, for example, the parent cell is an empty list.
    for entityType in CHILD_ENTITY_TYPES:
        vs = _replaceDetailSheet(newIndex, entityType)
        if vs:
            break


@FreqTableSheet.api
def zoomFreqtblRow(sheet, by):
    """
    Navigate a frequency table sheet, "zooming in" on matching rows from the
    source sheet. Open matching rows in a disposable sheet one level up
    in the stack - while using a split view, this means the non-active
    window is a dedicated zoom pane.
    """
    if sheet.cursorRowIndex == len(sheet.rows) - 1 and by == 1:
        vd.status("Already at the bottom!")
        return
    if sheet.cursorRowIndex == 0 and by == -1:
        vd.status("Already at the top!")
        return
    sheet.cursorDown(by)
    vs = sheet.openRow(sheet.cursorRow)
    vs.precious = False
    if sheet.source.source is vd.sheets[1].source and not vd.sheets[1].precious:
        vd.remove(vd.sheets[1])
    vd.sheets.insert(1, vs)


TableSheet.addCommand("", "next-parent-row", "sheet.goParentRow(1)")
TableSheet.addCommand("", "prev-parent-row", "sheet.goParentRow(-1)")

FreqTableSheet.addCommand("", "zoom-next-freqrow", "sheet.zoomFreqtblRow(1)")
FreqTableSheet.addCommand("", "zoom-prev-freqrow", "sheet.zoomFreqtblRow(-1)")
FreqTableSheet.addCommand("", "zoom-cur-freqrow", "sheet.zoomFreqtblRow(0)")
