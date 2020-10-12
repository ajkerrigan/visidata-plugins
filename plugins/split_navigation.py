from collections import namedtuple

from visidata import ALT, ENTER, FreqTableSheet, PyobjSheet, TableSheet, vd


class NoContentPlaceholder:
    emptyRowMessage = 'No content in parent row'
    emptyCellMessage = 'No content in parent cell'

    emptyRowSheet = None
    emptyCellSheet = None


def _noContent():
    '''
    Does the most recent status entry show an attempt to open an
    empty sheet?
    '''
    _, last_status_args, _ = vd.statusHistory[-1]
    return any(("no content" in arg for arg in last_status_args))


def _replaceDetailSheet(parentRowIdx, openCommand, placeholder):
    '''
    Try to refresh a child window with data from the given parent
    row.
    '''
    if vd.sheet is placeholder or openCommand in (
        cmd.longname for cmd in vd.sheet.cmdlog_sheet.rows
    ):
        parent = vd.sheets[1]
        vd.remove(vd.sheet)
        parent.cursorRowIndex = parentRowIdx
        parent.execCommand(openCommand)
        if vd.sheet is parent and _noContent():
            vd.push(NoContentPlaceholder.emptyCellSheet)
        return vd.sheet


@TableSheet.api
def goParentRow(sheet, by):
    '''
    While focused in a child "detail" split view, navigate through rows
    in the parent sheet.
    '''

    parent = vd.sheets[1]
    newIndex = parent.cursorRowIndex + by
    if newIndex < 0:
        vd.status('Already at the top!')
        return
    elif newIndex >= len(parent.rows):
        vd.status('Already at the bottom!')
        return

    if not NoContentPlaceholder.emptyRowSheet:
        NoContentPlaceholder.emptyRowSheet = PyobjSheet(
            'placeholder', NoContentPlaceholder.emptyRowMessage
        )
    if not NoContentPlaceholder.emptyCellSheet:
        NoContentPlaceholder.emptyCellSheet = PyobjSheet(
            'placeholder', NoContentPlaceholder.emptyCellMessage
        )

    # The goal here is to intelligently navigate around a parent window,
    # updating a child view in the process. Find out whether the current
    # sheet represents a detail view of the cursor _row_ or _cell_ in the
    # parent sheet. Use that to determine how to update the child view.
    #
    # Edge case:
    #
    # * When scrolling through parent cells that would yield no child content,
    #   we need a dummy stand-in sheet to keep the child window open.
    ChildUpdate = namedtuple('ChildUpdate', 'parentRowIdx openCommand placeholder')
    childUpdates = [
        ChildUpdate(newIndex, 'open-cell', NoContentPlaceholder.emptyCellSheet),
        ChildUpdate(newIndex, 'open-row', NoContentPlaceholder.emptyRowSheet),
    ]
    for childUpdate in childUpdates:
        vs = _replaceDetailSheet(*childUpdate)
        if vs:
            break


@FreqTableSheet.api
def zoomFreqtblRow(sheet, by):
    '''
    Navigate a frequency table sheet, "zooming in" on matching rows from the
    source sheet. Open matching rows in a disposable sheet one level up
    in the stack - while using a split view, this means the non-active
    window is a dedicated zoom pane.
    '''
    if sheet.cursorRowIndex == len(sheet.rows) - 1 and by == 1:
        vd.status('Already at the bottom!')
        return
    if sheet.cursorRowIndex == 0 and by == -1:
        vd.status('Already at the top!')
        return
    sheet.cursorDown(by)
    vs = sheet.openRow(sheet.cursorRow)
    vs.precious = False
    if sheet.source.source is vd.sheets[1].source and not vd.sheets[1].precious:
        vd.remove(vd.sheets[1])
    vd.sheets.insert(1, vs)


TableSheet.addCommand(ALT + 'j', 'next-parent-row', 'sheet.goParentRow(1)')
TableSheet.addCommand(ALT + 'k', 'prev-parent-row', 'sheet.goParentRow(-1)')

FreqTableSheet.addCommand(ALT + 'j', 'zoom-next-freqrow', 'sheet.zoomFreqtblRow(1)')
FreqTableSheet.addCommand(ALT + 'k', 'zoom-prev-freqrow', 'sheet.zoomFreqtblRow(-1)')
FreqTableSheet.addCommand(ALT + ENTER, 'zoom-cur-freqrow', 'sheet.zoomFreqtblRow(0)')
