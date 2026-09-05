# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Priority Areas — desktop map annotation for planning field validation.

The desktop mapper flags points, lines and polygons with a habitat class
and a check type (check boundary, check presence/absence, confirm class, ...)
so the field team knows where to focus. Annotations persist to a GeoPackage in
the project folder and travel with the project into the field.
"""

import os

from qgis.PyQt.QtGui import QIcon
# QAction / QActionGroup live in QtGui on Qt6, QtWidgets on Qt5.
try:
    from qgis.PyQt.QtGui import QAction, QActionGroup
except ImportError:
    from qgis.PyQt.QtWidgets import QAction, QActionGroup

from .priorityareas_map_tool import PriorityAreasMapTool
from .priorityareas_settings_dialog import SettingsDialog


class PriorityAreasPlugin:
    """QGIS plugin entry point."""

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)

        self.toolbar = None
        self.actions = []
        self.action_group = None
        self.map_tool = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initGui(self):
        self.map_tool = PriorityAreasMapTool(self.iface)

        self.toolbar = self.iface.addToolBar("Priority Areas")
        self.toolbar.setObjectName("Priority AreasToolbar")

        self.action_group = QActionGroup(self.iface.mainWindow())
        self.action_group.setExclusive(True)

        specs = [
            ("point",   "Priority Areas point",
             "Mark a spot for field validation"),
            ("line",    "Priority Areas line",
             "Draw a boundary or transect to check"),
            ("polygon", "Priority Areas area",
             "Define an area to prioritise for validation"),
        ]

        for mode, text, tip in specs:
            action = QAction(self._icon(mode), text, self.iface.mainWindow())
            action.setToolTip(tip)
            action.setCheckable(True)
            action.triggered.connect(self._make_activator(mode))
            self.action_group.addAction(action)
            self.toolbar.addAction(action)
            self.iface.addPluginToMenu("Priority Areas", action)
            self.actions.append(action)

        # Keep toolbar buttons in sync when the user switches to another tool.
        self.canvas.mapToolSet.connect(self._on_map_tool_set)

        # Settings — edit habitats, colours and check types.
        self.toolbar.addSeparator()
        self.action_settings = QAction(
            self._icon(
                "settings"), "Priority Areas settings…", self.iface.mainWindow()
        )
        self.action_settings.setToolTip(
            "Edit habitats, colours and check types")
        self.action_settings.triggered.connect(self._open_settings)
        self.toolbar.addAction(self.action_settings)
        self.iface.addPluginToMenu("Priority Areas", self.action_settings)
        self.actions.append(self.action_settings)

    def _icon(self, mode):
        """Per-geometry icon: icon_<mode>.png|svg if present, else the
        generic icon. Drop your own icon_point / icon_line / icon_polygon
        (PNG or SVG) into resources/ to override."""
        res = os.path.join(self.plugin_dir, "resources")
        for fname in ("icon_{}.png".format(mode), "icon_{}.svg".format(mode)):
            path = os.path.join(res, fname)
            if os.path.exists(path):
                return QIcon(path)
        return QIcon(os.path.join(res, "icon.svg"))

    def unload(self):
        try:
            self.canvas.mapToolSet.disconnect(self._on_map_tool_set)
        except (TypeError, RuntimeError):
            pass

        if self.map_tool is not None:
            self.canvas.unsetMapTool(self.map_tool)

        for action in self.actions:
            self.iface.removePluginMenu("Priority Areas", action)

        if self.toolbar is not None:
            del self.toolbar
            self.toolbar = None

        self.actions = []

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def _make_activator(self, mode):
        def activate(checked):
            if not checked:
                return
            self.map_tool.set_mode(mode)
            self.canvas.setMapTool(self.map_tool)
        return activate

    def _open_settings(self):
        dlg = SettingsDialog(self.iface, self.iface.mainWindow())
        dlg.exec()

    def _on_map_tool_set(self, new_tool, old_tool=None):
        if new_tool is not self.map_tool and self.action_group is not None:
            checked = self.action_group.checkedAction()
            if checked is not None:
                checked.setChecked(False)
