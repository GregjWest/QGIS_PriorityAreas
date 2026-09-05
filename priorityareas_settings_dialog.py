# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Settings dialog for Priority Areas.

Lets the user add / remove / rename habitats, pick each habitat's map colour,
and edit the check-type list. Saves to the vocabulary settings file (not the
.py). Renaming or removing values does not touch annotations already on the
map — that trade-off is surfaced as a warning and left to the user.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QListWidgetItem,
    QHeaderView,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
)
from qgis.gui import QgsColorButton

from . import priorityareas_vocabulary as vocab
from . import priorityareas_layers as layers

_FALLBACK_COLOR = "#888888"

# Qt5 / Qt6 enum compatibility
try:
    _EDITABLE = Qt.ItemFlag.ItemIsEditable
except AttributeError:
    _EDITABLE = Qt.ItemIsEditable

try:
    _STRETCH = QHeaderView.ResizeMode.Stretch
    _TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
except AttributeError:
    _STRETCH = QHeaderView.Stretch
    _TO_CONTENTS = QHeaderView.ResizeToContents

try:
    _BTN_SAVE = QDialogButtonBox.StandardButton.Save
    _BTN_CANCEL = QDialogButtonBox.StandardButton.Cancel
    _BTN_RESET = QDialogButtonBox.StandardButton.RestoreDefaults
except AttributeError:
    _BTN_SAVE = QDialogButtonBox.Save
    _BTN_CANCEL = QDialogButtonBox.Cancel
    _BTN_RESET = QDialogButtonBox.RestoreDefaults

try:
    _MSG_YES = QMessageBox.StandardButton.Yes
    _MSG_NO = QMessageBox.StandardButton.No
except AttributeError:
    _MSG_YES = QMessageBox.Yes
    _MSG_NO = QMessageBox.No


class SettingsDialog(QDialog):
    """Edit habitats (name + colour) and check types."""

    def __init__(self, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Priority Areas — Settings")
        self.setMinimumWidth(480)

        data = vocab.load()
        layout = QVBoxLayout(self)

        warning = QLabel(
            "Renaming or removing a habitat or check type here does not change "
            "annotations already saved on the map. Existing features keep their "
            "old value and may no longer match the styling or labels — updating "
            "or leaving them is up to you."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color:#7a5c00; background:#fff8e1; padding:8px;"
            "border:1px solid #ffe082; border-radius:4px;"
        )
        layout.addWidget(warning)

        # --- Habitats -------------------------------------------------
        hab_box = QGroupBox("Habitats  (name + map colour)")
        hab_layout = QVBoxLayout(hab_box)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Habitat", "Colour"])
        self.table.horizontalHeader().setSectionResizeMode(0, _STRETCH)
        self.table.horizontalHeader().setSectionResizeMode(1, _TO_CONTENTS)
        self.table.verticalHeader().setVisible(False)
        for entry in data["habitats"]:
            self._add_habitat_row(entry.get("name", ""), entry.get("color", _FALLBACK_COLOR))
        hab_layout.addWidget(self.table)

        hab_btns = QHBoxLayout()
        for label, slot in (
            ("Add", self._add_habitat_blank),
            ("Remove", self._remove_habitat),
            ("Up", lambda: self._move_habitat(-1)),
            ("Down", lambda: self._move_habitat(1)),
        ):
            b = QPushButton(label)
            b.clicked.connect(slot)
            hab_btns.addWidget(b)
        hab_btns.addStretch()
        hab_layout.addLayout(hab_btns)
        layout.addWidget(hab_box)

        # --- Check types ---------------------------------------------
        chk_box = QGroupBox("Check types  (double-click to rename)")
        chk_layout = QVBoxLayout(chk_box)

        self.list = QListWidget()
        for check in data["check_types"]:
            self._add_check_item(check)
        chk_layout.addWidget(self.list)

        chk_btns = QHBoxLayout()
        for label, slot in (
            ("Add", self._add_check_blank),
            ("Remove", self._remove_check),
            ("Up", lambda: self._move_check(-1)),
            ("Down", lambda: self._move_check(1)),
        ):
            b = QPushButton(label)
            b.clicked.connect(slot)
            chk_btns.addWidget(b)
        chk_btns.addStretch()
        chk_layout.addLayout(chk_btns)
        layout.addWidget(chk_box)

        # --- Apply-to-existing option --------------------------------
        self.chk_apply_existing = QCheckBox(
            "Update existing Priority Areas layers in this project when I save"
        )
        self.chk_apply_existing.setChecked(True)
        self.chk_apply_existing.setToolTip(
            "Re-applies colours and labels to annotation layers already loaded "
            "in the current project. Changes styling only, never the data."
        )
        layout.addWidget(self.chk_apply_existing)

        # --- Dialog buttons ------------------------------------------
        buttons = QDialogButtonBox(_BTN_SAVE | _BTN_CANCEL | _BTN_RESET)
        buttons.button(_BTN_SAVE).clicked.connect(self._save)
        buttons.button(_BTN_CANCEL).clicked.connect(self.reject)
        buttons.button(_BTN_RESET).clicked.connect(self._reset)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Habitat table helpers
    # ------------------------------------------------------------------

    def _add_habitat_row(self, name, color):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        button = QgsColorButton()
        button.setColor(QColor(color))
        button.setColorDialogTitle("Habitat colour")
        self.table.setCellWidget(row, 1, button)

    def _add_habitat_blank(self):
        self._add_habitat_row("New habitat", _FALLBACK_COLOR)
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)
        self.table.editItem(self.table.item(self.table.rowCount() - 1, 0))

    def _remove_habitat(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _habitats_from_table(self):
        out = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            name = item.text().strip() if item else ""
            button = self.table.cellWidget(row, 1)
            color = button.color().name() if button else _FALLBACK_COLOR
            out.append({"name": name, "color": color})
        return out

    def _repopulate_habitats(self, rows):
        self.table.setRowCount(0)
        for entry in rows:
            self._add_habitat_row(entry.get("name", ""), entry.get("color", _FALLBACK_COLOR))

    def _move_habitat(self, delta):
        row = self.table.currentRow()
        if row < 0:
            return
        rows = self._habitats_from_table()
        target = row + delta
        if target < 0 or target >= len(rows):
            return
        rows[row], rows[target] = rows[target], rows[row]
        self._repopulate_habitats(rows)
        self.table.setCurrentCell(target, 0)

    # ------------------------------------------------------------------
    # Check-type list helpers
    # ------------------------------------------------------------------

    def _add_check_item(self, text):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | _EDITABLE)
        self.list.addItem(item)

    def _add_check_blank(self):
        self._add_check_item("New check type")
        item = self.list.item(self.list.count() - 1)
        self.list.setCurrentItem(item)
        self.list.editItem(item)

    def _remove_check(self):
        row = self.list.currentRow()
        if row >= 0:
            self.list.takeItem(row)

    def _move_check(self, delta):
        row = self.list.currentRow()
        if row < 0:
            return
        target = row + delta
        if target < 0 or target >= self.list.count():
            return
        item = self.list.takeItem(row)
        self.list.insertItem(target, item)
        self.list.setCurrentRow(target)

    # ------------------------------------------------------------------
    # Save / reset
    # ------------------------------------------------------------------

    def _save(self):
        habitats = [h for h in self._habitats_from_table() if h["name"]]
        checks = []
        for i in range(self.list.count()):
            text = self.list.item(i).text().strip()
            if text:
                checks.append(text)

        if not habitats:
            QMessageBox.warning(self, "Priority Areas", "You need at least one habitat.")
            return
        if not checks:
            QMessageBox.warning(self, "Priority Areas", "You need at least one check type.")
            return
        if len({h["name"].lower() for h in habitats}) != len(habitats):
            QMessageBox.warning(self, "Priority Areas", "Habitat names must be unique.")
            return
        if len({c.lower() for c in checks}) != len(checks):
            QMessageBox.warning(self, "Priority Areas", "Check types must be unique.")
            return

        if not vocab.save({"habitats": habitats, "check_types": checks}):
            QMessageBox.critical(
                self, "Priority Areas", "Could not write the settings file."
            )
            return

        if self.chk_apply_existing.isChecked():
            try:
                restyled = layers.restyle_project_layers()
            except Exception:
                restyled = 0
            if restyled and self.iface is not None:
                self.iface.mapCanvas().refresh()

        self.accept()

    def _reset(self):
        answer = QMessageBox.question(
            self,
            "Priority Areas",
            "Reset habitats and check types to the plugin defaults?",
            _MSG_YES | _MSG_NO,
        )
        if answer != _MSG_YES:
            return
        data = vocab.defaults()
        self._repopulate_habitats(data["habitats"])
        self.list.clear()
        for check in data["check_types"]:
            self._add_check_item(check)
