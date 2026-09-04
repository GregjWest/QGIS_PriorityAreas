# -*- coding: utf-8 -*-
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
    "Posidonia/Zostera",
    "Zostera",
    "Halophila",
    "Mangrove",
    "Saltmarsh",
    "Seagrass",
    "Other",
]

HABITAT_COLORS = {
    "Posidonia": "#c40000",   # Red
    "Posidonia/Zostera": "#fc03f0",   # Pink
    "Zostera":   "#0EC7FF",   # Light blue
    "Halophila": "#FF9900",   # Orange
    "Mangrove":  "#13DF00",   # Bright green
    "Saltmarsh": "#D6C100",   # gold
    "Seagrass":  "#26EECD",   # cyan (generic seagrass)
    "Other":     "#8C00FF",   # purple
}

DEFAULT_HABITAT = "Posidonia"

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
    "Photo",
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
