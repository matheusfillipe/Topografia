# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TopoGrafia
                                 A QGIS plugin
 TOPO
                             -------------------
        begin                : 2017-02-07
        copyright            : (C) 2017 by Lucas
        email                : lucaophp@hotmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
def name(): 
    return "GeoRoad"
def description():
    return "Utilitario desenvolvido pela UFV para facilitar a vida do profissional de topográfia."
def version(): 
    return "Version 0.4.0" 
def qgisMinimumVersion():
    return "3.0"

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TopoGrafia class from file TopoGrafia.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
#    import sys
#    import os
#    path=os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
#    path="~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/Topografia/"
#    sys.path.append(path)


    from .main import TopoGrafia
    return TopoGrafia(iface)
