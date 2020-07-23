from contextlib import suppress
from visidata import (
    TableSheet,
    FreqTableSheet,
    load_pyobj,
    vd,
    ENTER,
)


class NoContentPlaceholders:
    empty_row_message = 'No content in parent row'
    empty_cell_message = 'No content in parent cell'

    empty_row_sheet = None
    empty_cell_sheet = None


@TableSheet.api
def go_parent_row(sheet, by):
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

    # Hoo boy this is ugly, but it's useful enough to leave in and hopefully
    # clean up later.
    #
    # The idea is to try to intelligently navigate around a parent based
    # on the content of a child window. So:
    #
    # * If the child window's contents look like the parent window's cursor
    #   row, move the cursor in the parent window and load the new cursor row.
    #
    # * If the child contents look like they came from the cursor _cell_ in
    #   the parent window, move the parent window cursor and load the cursor cell.
    #
    # Some edge cases that led to this quirky implementation:
    #
    # * Null values in a parent window may be left out of the child window,
    #   so include subset checks for the contents.
    #
    # * Not all content is hashable, so leave set logic until the end of
    #   a comparison and suppress type errors.
    #
    # * When scrolling through parent cells that would yield no content,
    #   we need a stand-in for content that keeps a child window open and
    #   also gives a hint about how to handle the next parent move action.
    #   (Should we move and then load the row or cell?)
    with suppress(TypeError):
        if (
            sheet is NoContentPlaceholders.empty_cell_sheet
            or sheet.rows == parent.cursorCell.value
            or set(sheet.rows) <= set(parent.cursorCell.value)
        ):
            parent.cursorRowIndex = newIndex
            newSheet = (
                parent.openCell(parent.cursorCol, parent.cursorRow)
                or NoContentPlaceholders.empty_cell_sheet
            )
            if not newSheet:
                NoContentPlaceholders.empty_cell_sheet = newSheet = load_pyobj(
                    'placeholder', NoContentPlaceholders.empty_cell_message
                )
            vd.replace(newSheet)
            return

    with suppress(TypeError):
        if (
            sheet is NoContentPlaceholders.empty_row_sheet
            or [col.getTypedValue(col.sheet.cursorRow) for col in parent.columns]
            == [sheet.cursorCol.getTypedValue(row) for row in sheet.rows]
            or (sheet.keyCols and set(sheet.keyCols[0].getValues(sheet.rows))
            <= {c.name for c in parent.columns})
        ):
            parent.cursorRowIndex = newIndex
            newSheet = (
                parent.openRow(parent.cursorRow) or NoContentPlaceholders.empty_row_sheet
            )
            if not newSheet:
                NoContentPlaceholders.empty_row_sheet = newSheet = load_pyobj(
                    'placeholder', NoContentPlaceholders.empty_row_message
                )
            vd.replace(newSheet)
            return


@FreqTableSheet.api
def zoom_freqtbl_row(sheet, by):
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


TableSheet.addCommand('^[j', 'next-parent-row', 'sheet.go_parent_row(1)')
TableSheet.addCommand('^[k', 'prev-parent-row', 'sheet.go_parent_row(-1)')

FreqTableSheet.addCommand('^[j', 'zoom-next-freqrow', 'sheet.zoom_freqtbl_row(1)')
FreqTableSheet.addCommand('^[k', 'zoom-prev-freqrow', 'sheet.zoom_freqtbl_row(-1)')
FreqTableSheet.addCommand('^[' + ENTER, 'zoom-cur-freqrow', 'sheet.zoom_freqtbl_row(0)')
