#  -------------------------------------------------------------------------
#  pyCGNS - Python package for CFD General Notation System -
#  See license.txt file in the root directory of this Python module source
#  -------------------------------------------------------------------------
#
"""
 implementation info:

   All Q7***Window(s) are created using Qt Designer,
   each produces a Ui_Q7***Window as Cython class,
   which is wrapped by a Q7*** python class.
   This latter is the one to use with Python.
   Same with stuff like Widgets.

   The Q7fingerPrint is the actual class with all CGNS tree info,
   including the list of views and selections. It is more or less
   the model itself but with some of local stuff and I want two
   separate classes.
"""


def show(T, *args):
    from qtpy.QtWidgets import QApplication
    from CGNS.NAV.woption import Q7Option
    from CGNS.NAV.wtree import Q7Tree
    from CGNS.NAV.mtree import Q7TreeModel
    from CGNS.NAV.wfingerprint import Q7FingerPrint

    def dummy(*args):
        pass

    app = QApplication(args)

    app.updateViews = dummy
    app.removeTreeStatus = dummy
    app.addTreeStatus = dummy
    app.loadOptions = dummy
    app.addLine = dummy
    app.delLine = dummy
    app.transientRecurse = False
    app.transientVTK = False

    app.verbose = True
    app._application = app
    app.wOption = Q7Option(app)
    app.wOption.reset()
    app.processEvents()

    fgprint = Q7FingerPrint(app, '.', '<run-time>', T, [], [])
    Q7TreeModel(fgprint.index)
    child = Q7Tree(app, '/', fgprint.index)

    for wg in [child.bSave, child.bQueryView, child.bSaveAs, child.bInfo,
               child.bCheck, child.bCheckList, child.bClearChecks,
               child.bPatternView, child.bToolsView, child.bFormView,
               child.bSelectLinkSrc, child.bSelectLinkDst,
               child.bBackControl]:
        wg.setEnabled(False)

    fgprint._status = [Q7FingerPrint.STATUS_MODIFIED]
    child.show()

    app.exec_()

# --- last line
