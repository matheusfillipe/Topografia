# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TopoGrafia
                                 A QGIS plugin
 TOPO
                              -------------------
        begin                : 2017-02-07
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Lucas
        email                : lucaophp@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Initialize Qt resources from file resources.py
# Import the code for the dialog
import os.path
from qgis.utils import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtGui import QAction


import resources
from app.controller.config import Config
from app.controller.estacas import Estacas


class TopoGrafia:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TopoGrafia_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Topografia')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'TopoGrafia')
        self.toolbar.setObjectName(u'TopoGrafia')
        # -----------------------------------------------
        #instancia do controller de config
        self.conf = Config(iface)
        '''
            Elemento dialogo.
        '''
        '''self.dlg = TopoGrafiaDialog()'''

        self.estacas = Estacas(iface)



        # combo.addItems(["%d - %s" % (x[1], x[0]) for x in self.rowsCRS])

    def changeCRS(self):
        self.conf.changeCRS()



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TopoGrafia', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        '''self.dlg = TopoGrafiaDialog()'''

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path_map = ':/plugins/TopoGrafia/app/resources/icons/iconmap.png'
        icon_path_carta = ':/plugins/TopoGrafia/app/resources/icons/iconcarta.png'
        icon_path_curva = ':/plugins/TopoGrafia/app/resources/icons/iconcurva.png'
        icon_path_tools = ':/plugins/TopoGrafia/app/resources/icons/icontools.png'
        icon_path_open = ':/plugins/TopoGrafia/app/resources/icons/iconopen.png'
        icon_path_save = ':/plugins/TopoGrafia/app/resources/icons/iconsave.png'
        icon_path = ':/plugins/TopoGrafia/app/resources/icons/iconnew.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Novo Arquivo Topografico'),
            callback=self.conf.newfile,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path_open,
            text=self.tr(u'Abrir Arquivo Topografico'),
            callback=self.conf.openfile,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path_save,
            text=self.tr(u'Salvar Arquivo Topografico'),
            callback=self.conf.savefile,
            parent=self.iface.mainWindow())

        self.changeCRS()
        self.add_action(
            icon_path_tools,
            text=self.tr(u'Configurações Geograficas'),
            callback=self.conf.run,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path_map,
            text=self.tr(u'Abrir Mapa'),
            callback=self.conf.carregamapa,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path_carta,
            text=self.tr(u'Abrir Cartas'),
            callback=self.conf.carregacarta,
            parent=self.iface.mainWindow()
        )

        self.add_action(
            icon_path_curva,
            text=self.tr(u'Curvas Horizontais em tabela'),
            callback=self.run_tracado,
            parent=self.iface.mainWindow()
        )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Topografia'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run_tracado(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if not self.conf.savefile() is None:
            self.estacas.run()

    def run(self):
        pass

