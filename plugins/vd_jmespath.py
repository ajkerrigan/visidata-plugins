from functools import partial
from hashlib import sha1

import jmespath
from visidata import BaseSheet, ExprColumn, vd


@BaseSheet.api
def addcol_jmespath(sheet):
    try:
        completer = vd.CompleteExpr
    except AttributeError:
        vd.debug("falling back to global for CompleteExpr")
        from visidata import CompleteExpr

        completer = CompleteExpr
    expr = vd.input(
        "new column jmespath expression=",
        "jmespath-expr",
        completer=completer(sheet),
    )
    # Create a partial function based on the provided jmespath expression,
    # and add it as a sheet attribute. This is one way to avoid edge cases
    # when evaluating jmespath expressions that contain nested quotes.
    partial_attr = f"_jmespath_search_{sha1(expr.encode('utf8')).hexdigest()}"
    setattr(sheet, partial_attr, partial(jmespath.search, expr))
    sheet.addColumnAtCursor(
        ExprColumn(expr, expr=f"sheet.{partial_attr}(row)", curcol=sheet.cursorCol)
    )


@BaseSheet.api
def select_by_jmespath(sheet, unselect=False):
    action = "unselect" if unselect else "select"
    expr = vd.input(
        f"{action} by jmespath expression=",
        "jmespath-expr",
        completer=vd.CompleteExpr(sheet),
    )

    match_func = partial(jmespath.search, expr)
    select_func = getattr(sheet, action)
    select_func(sheet.gatherBy(match_func), progress=False)


BaseSheet.addCommand(
    "",
    "addcol-jmespath",
    "sheet.addcol_jmespath()",
    "create new column from a jmespath expression",
)
BaseSheet.addCommand(
    "",
    "select-jmespath",
    "sheet.select_by_jmespath()",
    "select rows matching a jmespath expression in any visible column",
)
BaseSheet.addCommand(
    "",
    "unselect-jmespath",
    "sheet.select_by_jmespath(unselect=True)",
    "unselect rows matching a jmespath expression in any visible column",
)

vd.addGlobals(globals())
