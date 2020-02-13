'''
Convert lists of Key/Value pairs to dicts, or vice versa. Inspired by
the from_entries and to_entries functions in jq:

https://stedolan.github.io/jq/manual/#to_entries,from_entries,with_entries
'''

from visidata import vd, Column, SettableColumn, Sheet


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

    def _die():
        sheet.columns.pop(new_idx)
        vd.fail(f'Columns {col.name} is not a list of Key/Value pairs')

    new_idx = sheet.columns.index(col) + 1
    new_col = sheet.addColumn(SettableColumn(col.name), index=new_idx)
    for r in rows:
        v = col.getValue(r)
        if not isinstance(v, list):
            _die()
        try:
            new_col.setValue(r, {entry['Key']: entry['Value'] for entry in v})
        except KeyError:
            _die()
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
    new_col = sheet.addColumn(SettableColumn(col.name), index=new_idx)
    for r in rows:
        val = col.getValue(r)
        if not isinstance(val, dict):
            sheet.columns.pop(new_idx)
            vd.fail('Column "{}" is not a dict'.format(col.name))
        new_col.setValue(r, [{'Key': k, 'Value': v} for k, v in val.items()])
    col.hide()
    return new_col


Sheet.addCommand("z(", "setcol-fromentries", "cursorCol.from_entries()")
Sheet.addCommand("z)", "setcol-toentries", "cursorCol.to_entries()")
