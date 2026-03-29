import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from .dashboard_dock import DashboardDock


class LayerDashboardPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock = None
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        self.action = QAction(icon, "Layer Dashboard", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle)
        
        self.iface.addPluginToVectorMenu("Layer Dashboard", self.action)
        self.iface.addToolBarIcon(self.action)

        self.dock = DashboardDock(self.iface)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()
        self.dock.visibilityChanged.connect(self.action.setChecked)

    def unload(self):
        self.iface.removePluginVectorMenu("Layer Dashboard", self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()

    def toggle(self, checked):
        if checked:
            self.dock.show()
            self.dock.raise_()
            self.dock.populate_layers()
        else:
            self.dock.hide()
