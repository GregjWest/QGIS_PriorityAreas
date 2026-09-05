# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Priority Areas configuration.

Edit this one file to reshape the tool's vocabulary. The habitat classes the
desktop mapper picks from, the colours those classes draw with, and the check
types the field team act on all live here. Change these and the dialog, the
stored values and the legend follow.
"""

# ----------------------------------------------------------------------
# Habitat — the primary selector. Drives the map colour so each habitat
# class reads at a glance. Order here is the order shown in the dialog.
# ----------------------------------------------------------------------
HABITATS = [
    "Posidonia",
    "Zostera",
    "Mangrove",
    "Saltmarsh",
    "Seagrass",
    "Other",
]

HABITAT_COLORS = {
    "Posidonia": "#ff0080",   # Red
    "Zostera":   "#0BF5FD",   # Light blue
    "Mangrove":  "#13DF00",   # Bright green
    "Saltmarsh": "#FFBD17",   # gold
    "Seagrass":  "#00ACC1",   # cyan (generic seagrass)
    "Other":     "#8C00FF",   # purple
}

DEFAULT_HABITAT = "Posidonia"

# ----------------------------------------------------------------------
# Check type — what the field ops team needs to look at. Used as the label.
# ----------------------------------------------------------------------
CHECK_TYPES = [
    "Check boundary",
    "Check presence/absence",
    "Check density/condition",
    "Confirm classification",
    "Mooring scar check",
    "Possible dieback",
    "Drone area",
    "Other",
]

DEFAULT_CHECK_TYPE = "Check boundary"

# ----------------------------------------------------------------------
# Storage — a GeoPackage in the project folder, one layer per geometry
# type, grouped in the layer tree.
# ----------------------------------------------------------------------
GPKG_NAME = "PriorityAreas.gpkg"
GROUP_NAME = "Priority Areas"
LAYER_POINT = "POINTS"
LAYER_LINE = "LINES"
LAYER_POLY = "POLYGONS"
