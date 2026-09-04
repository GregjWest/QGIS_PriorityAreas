# -*- coding: utf-8 -*-
"""
Priority Areas annotation dialog.

Shown after a point/line/polygon is drawn. Captures the habitat class, the
check type the field team should act on, and a free-text note.
The last-used habitat/check type are passed in so the mapper can rattle
through many flags without re-picking each time.
"""

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QPlainTextEdit,
    QDialogButtonBox,
)

from .priorityareas_config import (
    HABITATS,
    CHECK_TYPES,
)

# Standard-button enum: scoped under StandardButton in Qt6, unscoped in Qt5.
try:
    _BTN_OK = QDialogButtonBox.StandardButton.Ok
    _BTN_CANCEL = QDialogButtonBox.StandardButton.Cancel
except AttributeError:
    _BTN_OK = QDialogButtonBox.Ok
    _BTN_CANCEL = QDialogButtonBox.Cancel


class PriorityAreasDialog(QDialog):
    """Collect Priority Areas attributes for a freshly drawn feature."""

    def __init__(self, geom_label, defaults, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Priority Areas annotation — {}".format(geom_label))
        self.setMinimumWidth(360)

        check_default = defaults.get("check_type")
        habitat_default = defaults.get("habitat")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_habitat = QComboBox()
        self.cmb_habitat.addItems(HABITATS)
        self._select(self.cmb_habitat, habitat_default)

        self.cmb_check = QComboBox()
        self.cmb_check.addItems(CHECK_TYPES)
        self._select(self.cmb_check, check_default)

        self.txt_note = QPlainTextEdit()
        self.txt_note.setPlaceholderText(
            "Optional note for the field team (what to look for, why it matters)…"
        )
        self.txt_note.setFixedHeight(80)

        form.addRow("Habitat", self.cmb_habitat)
        form.addRow("Check type", self.cmb_check)
        form.addRow("Note", self.txt_note)

        layout.addLayout(form)

        buttons = QDialogButtonBox(_BTN_OK | _BTN_CANCEL)
        buttons.button(_BTN_OK).setText("Add annotation")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.cmb_habitat.setFocus()

    @staticmethod
    def _select(combo, value):
        if value is None:
            return
        idx = combo.findText(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def values(self):
        """Return the entered attributes as a dict."""
        return {
            "habitat":    self.cmb_habitat.currentText(),
            "check_type": self.cmb_check.currentText(),
            "note":       self.txt_note.toPlainText().strip(),
        }
