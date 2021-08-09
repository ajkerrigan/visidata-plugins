from functools import partial
import jmespath
from visidata import BaseSheet, ExprColumn, vd


@BaseSheet.api
def addcol_jmespath(sheet):
    expr = sheet.inputExpr("new column jmespath expression=")
    sheet.addColumnAtCursor(
        ExprColumn(
            expr,
            expr=f"jmespath.search('{expr}', row)",
            curcol=sheet.cursorCol
        )
    )

@BaseSheet.api
def select_by_jmespath(sheet, unselect=False):
    action = 'unselect' if unselect else 'select'
    expr = sheet.inputExpr(f"{action} by jmespath expression=")

    match_func = partial(jmespath.search, expr)
    select_func = getattr(sheet, action)
    select_func(sheet.gatherBy(match_func), progress=False)

BaseSheet.addCommand(
    '',
    'addcol-jmespath',
    'sheet.addcol_jmespath()',
    'create new column from a jmespath expression'
)
BaseSheet.addCommand(
    '',
    'select-jmespath',
    'sheet.select_by_jmespath()',
    'select rows matching a jmespath expression in any visible column'
)
BaseSheet.addCommand(
    '',
    'unselect-jmespath',
    'sheet.select_by_jmespath(unselect=True)',
    'unselect rows matching a jmespath expression in any visible column'
)

vd.addGlobals(globals())
