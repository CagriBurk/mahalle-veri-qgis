"""QGIS plugin entry: one menu item and one toolbar button that open the dialog."""

from __future__ import annotations

from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

MENU = "&Mahalle Veri"


class MahalleVeriPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self) -> None:
        icon = QIcon(str(Path(__file__).with_name("icon.svg")))
        self.action = QAction(icon, "Mahalle veri paketini yükle…", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToVectorMenu(MENU, self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self) -> None:
        if self.action is not None:
            self.iface.removePluginVectorMenu(MENU, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

    def run(self) -> None:
        from .dialog import LoadDialog

        if self.dialog is None:
            self.dialog = LoadDialog(self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
