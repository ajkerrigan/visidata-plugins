'''
Convert lists of Key/Value pairs to dicts, or vice versa. Inspired by
the from_entries and to_entries functions in jq:

https://stedolan.github.io/jq/manual/#to_entries,from_entries,with_entries
'''

from visidata import Column, SettableColumn, Sheet, vd

def _isNullFunc():
    '''
    isNullFunc is available as a sheet property in newer VisiData releases, but
    was previously a function in the "visidata" module. Try to use the sheet
    property, but fall back to support earlier versions.
    '''
    try:
        return vd.sheet.isNullFunc()
    except AttributeError:
        import visidata
        return visidata.isNullFunc()

@Column.api
def from_entries(col):
    '''
    Convert values from lists of Key/Value pairs into a dict, similar
    to the from_entries function in jq.

    Abort if the specified column's value for any row is _not_ a list of Key/Value
    pairs.
    '''
    sheet = col.sheet
    rows = sheet.rows

    key_keynames = ('key', 'name')
    NOT_FOUND = object()

    def _die():
        sheet.columns.pop(new_idx)
        vd.fail(f'Columns {col.name} is not a list of Key/Value pairs')

    new_idx = sheet.columns.index(col) + 1
    new_col = SettableColumn(col.name)
    sheet.addColumn(new_col, index=new_idx)
    isNull = _isNullFunc()
    for row in rows:
        val = col.getValue(row)
        new_val = {}
        if isNull(val):
            continue
        if not isinstance(val, list):
            _die()
        for pair in val:
            col_key = col_value = NOT_FOUND
            for k, v in pair.items():
                if k.lower() in key_keynames:
                    col_key = v
                elif k.lower() == 'value':
                    col_value = v
            if col_key is NOT_FOUND or col_value is NOT_FOUND:
                _die()
            new_val[col_key] = col_value
        new_col.setValue(row, new_val)
    col.hide()
    return new_col


@Column.api
def to_entries(col):
    '''
    Convert values from a dict into a list of Key/Value pairs, similar
    to the to_entries function in jq:

    Abort if the specified column's value for any row is _not_ a dict.
    '''
    sheet = col.sheet
    rows = sheet.rows

    new_idx = sheet.columns.index(col) + 1
    new_col = SettableColumn(col.name)
    sheet.addColumn(new_col, index=new_idx)
    isNull = _isNullFunc()
    for r in rows:
        val = col.getValue(r)
        if isNull(val):
            continue
        if not isinstance(val, dict):
            sheet.columns.pop(new_idx)
            vd.fail('Column "{}" is not a dict'.format(col.name))
        new_col.setValue(r, [{'Key': k, 'Value': v} for k, v in val.items()])
    col.hide()
    return new_col


Sheet.addCommand("z{", "setcol-fromentries", "cursorCol.from_entries()")
Sheet.addCommand("z}", "setcol-toentries", "cursorCol.to_entries()")
