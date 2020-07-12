from visidata import TableSheet, FreqTableSheet, load_pyobj, vd, ENTER

@TableSheet.api
def go_dict_row(sheet, by):
    '''
    While focused in a child "detail" split view, navigate through rows
    in the parent sheet.
    '''
    parent = vd.sheets[1]
    newIndex = parent.cursorRowIndex + by
    if newIndex < 0:
        vd.status('Already at the top!')
    elif newIndex >= len(parent.rows):
        vd.status('Already at the bottom!')
    else:
        parent.cursorRowIndex = newIndex
        vd.replace(
            load_pyobj(f'{parent.name}[{parent.cursorRowIndex}]', parent.cursorRow)
        )

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

TableSheet.addCommand('^[j', 'next-dict-row', 'sheet.go_dict_row(1)')
TableSheet.addCommand('^[k', 'prev-dict-row', 'sheet.go_dict_row(-1)')

FreqTableSheet.addCommand('^[j', 'zoom-next-freqrow', 'sheet.zoom_freqtbl_row(1)')
FreqTableSheet.addCommand('^[k', 'zoom-prev-freqrow', 'sheet.zoom_freqtbl_row(-1)')
FreqTableSheet.addCommand('^['+ENTER, 'zoom-cur-freqrow', 'sheet.zoom_freqtbl_row(0)')
