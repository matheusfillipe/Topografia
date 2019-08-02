from ..Qt import QtGui
from ..graphicsItems.GraphicsLayout import GraphicsLayout
from .GraphicsView import GraphicsView

__all__ = ['GraphicsLayoutWidget']
class GraphicsLayoutWidget(GraphicsView):
    """
    Convenience class consisting of a :class:`GraphicsView 
    <PyQtGraph.GraphicsView>` with a single :class:`GraphicsLayout
    <PyQtGraph.GraphicsLayout>` as its central item.

    This class wraps several methods from its internal GraphicsLayout:
    :func:`nextRow <PyQtGraph.GraphicsLayout.nextRow>`
    :func:`nextColumn <PyQtGraph.GraphicsLayout.nextColumn>`
    :func:`addPlot <PyQtGraph.GraphicsLayout.addPlot>`
    :func:`addViewBox <PyQtGraph.GraphicsLayout.addViewBox>`
    :func:`addItem <PyQtGraph.GraphicsLayout.addItem>`
    :func:`getItem <PyQtGraph.GraphicsLayout.getItem>`
    :func:`addLabel <PyQtGraph.GraphicsLayout.addLabel>`
    :func:`addLayout <PyQtGraph.GraphicsLayout.addLayout>`
    :func:`removeItem <PyQtGraph.GraphicsLayout.removeItem>`
    :func:`itemIndex <PyQtGraph.GraphicsLayout.itemIndex>`
    :func:`clear <PyQtGraph.GraphicsLayout.clear>`
    """
    def __init__(self, parent=None, **kargs):
        GraphicsView.__init__(self, parent)
        self.ci = GraphicsLayout(**kargs)
        for n in ['nextRow', 'nextCol', 'nextColumn', 'addPlot', 'addViewBox', 'addItem', 'getItem', 'addLayout', 'addLabel', 'removeItem', 'itemIndex', 'clear']:
            setattr(self, n, getattr(self.ci, n))
        self.setCentralItem(self.ci)
