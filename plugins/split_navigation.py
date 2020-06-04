from visidata import BaseSheet, load_pyobj, vd


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


BaseSheet.addCommand('^[j', 'next-dict-row', f'{__name__}.go_dict_row(sheet, 1)')
BaseSheet.addCommand('^[k', 'prev-dict-row', f'{__name__}.go_dict_row(sheet, -1)')
