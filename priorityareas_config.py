# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Priority Areas — default vocabulary.

These values are the DEFAULTS. On first run they seed a settings file in your
QGIS profile (PriorityAreas/vocabulary.json); after that, the plugin reads the
vocabulary from there, and the Settings dialog (or hand-editing that JSON) is
how you change habitats, colours and check types. Editing this file only
changes what a fresh install / a "Reset to defaults" starts from.

The storage names at the bottom are not user-editable and are read from here.
"""

# ----------------------------------------------------------------------
# Habitat — the primary selector. Drives the map colour so each habitat
# class reads at a glance. Order here is the order shown in the dialog.
# ----------------------------------------------------------------------
HABITATS = [
    "Posidonia",
    "Posidonia/Zostera",
    "Zostera",
    "Halophila",
    "Mangrove",
    "Saltmarsh",
    "Seagrass",
    "Other",
]

HABITAT_COLORS = {
    "Posidonia": "#ff0000",   # Red
    "Posidonia/Zostera":  "#e100ff",  # Pink
    "Zostera":   "#008CFF",   # Light blue
    "Halophila": "#FFAE00",   # Orange
    "Mangrove":  "#13DF00",   # Bright green
    "Saltmarsh": "#B8B503",   # gold
    "Seagrass":  "#00ACC1",   # cyan (generic seagrass)
    "Other":     "#8C00FF",   # purple
}

# ----------------------------------------------------------------------
# Check type — what the field ops team needs to look at. Used as the label.
# ----------------------------------------------------------------------
CHECK_TYPES = [
    "Check boundary",
    "Check presence/absence",
    "Check classification and boundary",
    "Check density/condition",
    "Confirm classification",
    "Mooring scar check",
    "Possible dieback",
    "Mangrove - Drone area",
    "Saltmarsh - Drone area",
    "Drone area",
    "Video",
    "Other",
]

# ----------------------------------------------------------------------
# Storage — a GeoPackage in the project folder, one layer per geometry
# type, grouped in the layer tree.
# ----------------------------------------------------------------------
GPKG_NAME = "PriorityAreas.gpkg"
GROUP_NAME = "Priority Areas"
LAYER_POINT = "POINTS"
LAYER_LINE = "LINES"
LAYER_POLY = "POLYGONS"
