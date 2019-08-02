# -*- coding: utf-8 -*-
"""
PlotWidget.py -  Convenience class--GraphicsView widget displaying a single PlotItem
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from ..Qt import QtCore, QtGui
from .GraphicsView import *
from ..graphicsItems.PlotItem import *

__all__ = ['PlotWidget']
class PlotWidget(GraphicsView):
    
    # signals wrapped from PlotItem / ViewBox
    sigRangeChanged = QtCore.Signal(object, object)
    sigTransformChanged = QtCore.Signal(object)
    
    """
    :class:`GraphicsView <PyQtGraph.GraphicsView>` widget with a single 
    :class:`PlotItem <PyQtGraph.PlotItem>` inside.
    
    The following methods are wrapped directly from PlotItem: 
    :func:`addItem <PyQtGraph.PlotItem.addItem>`, 
    :func:`removeItem <PyQtGraph.PlotItem.removeItem>`, 
    :func:`clear <PyQtGraph.PlotItem.clear>`, 
    :func:`setXRange <PyQtGraph.ViewBox.setXRange>`,
    :func:`setYRange <PyQtGraph.ViewBox.setYRange>`,
    :func:`setRange <PyQtGraph.ViewBox.setRange>`,
    :func:`autoRange <PyQtGraph.ViewBox.autoRange>`,
    :func:`setXLink <PyQtGraph.ViewBox.setXLink>`,
    :func:`setYLink <PyQtGraph.ViewBox.setYLink>`,
    :func:`viewRect <PyQtGraph.ViewBox.viewRect>`,
    :func:`setMouseEnabled <PyQtGraph.ViewBox.setMouseEnabled>`,
    :func:`enableAutoRange <PyQtGraph.ViewBox.enableAutoRange>`,
    :func:`disableAutoRange <PyQtGraph.ViewBox.disableAutoRange>`,
    :func:`setAspectLocked <PyQtGraph.ViewBox.setAspectLocked>`,
    :func:`setLimits <PyQtGraph.ViewBox.setLimits>`,
    :func:`register <PyQtGraph.ViewBox.register>`,
    :func:`unregister <PyQtGraph.ViewBox.unregister>`
    
    
    For all 
    other methods, use :func:`getPlotItem <PyQtGraph.PlotWidget.getPlotItem>`.
    """
    def __init__(self, parent=None, background='default', **kargs):
        """When initializing PlotWidget, *parent* and *background* are passed to 
        :func:`GraphicsWidget.__init__() <PyQtGraph.GraphicsWidget.__init__>`
        and all others are passed
        to :func:`PlotItem.__init__() <PyQtGraph.PlotItem.__init__>`."""
        GraphicsView.__init__(self, parent, background=background)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.enableMouse(False)
        self.plotItem = PlotItem(**kargs)
        self.setCentralItem(self.plotItem)
        ## Explicitly wrap methods from plotItem
        ## NOTE: If you change this list, update the documentation above as well.
        for m in ['addItem', 'removeItem', 'autoRange', 'clear', 'setXRange', 
                  'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled', 
                  'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange', 
                  'setLimits', 'register', 'unregister', 'viewRect']:
            setattr(self, m, getattr(self.plotItem, m))
        #QtCore.QObject.connect(self.plotItem, QtCore.SIGNAL('viewChanged'), self.viewChanged)
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)
    
    def close(self):
        self.plotItem.close()
        self.plotItem = None
        #self.scene().clear()
        #self.mPlotItem.close()
        self.setParent(None)
        super(PlotWidget, self).close()

    def __getattr__(self, attr):  ## implicitly wrap methods from plotItem
        if hasattr(self.plotItem, attr):
            m = getattr(self.plotItem, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)
    
    def viewRangeChanged(self, view, range):
        #self.emit(QtCore.SIGNAL('viewChanged'), *args)
        self.sigRangeChanged.emit(self, range)

    def widgetGroupInterface(self):
        return (None, PlotWidget.saveState, PlotWidget.restoreState)

    def saveState(self):
        return self.plotItem.saveState()
        
    def restoreState(self, state):
        return self.plotItem.restoreState(state)
        
    def getPlotItem(self):
        """Return the PlotItem contained within."""
        return self.plotItem
        
        
        