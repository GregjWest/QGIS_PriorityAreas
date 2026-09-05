# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Layer plumbing for Priority Areas.

Creates/loads the Priority Areas layers inside a GeoPackage in the project folder,
defines the shared attribute schema, and builds the habitat-driven
categorized styling + labelling. Kept separate from the map tool so the
drawing logic stays lean.
"""

import os

from qgis.core import (
    QgsProject,
    Qgis,
    QgsVectorLayer,
    QgsField,
    QgsFields,
    QgsWkbTypes,
    QgsVectorFileWriter,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

# Field-type tokens. Qt6 removed the QVariant.Type members (QVariant.String
# etc.), so on Qt6 use QMetaType; on Qt5 keep QVariant for QGIS 3.16 support.
from qgis.PyQt.QtCore import QVariant
try:
    _T_STRING = QVariant.String
    _T_DOUBLE = QVariant.Double
    _T_INT = QVariant.Int
except AttributeError:
    from qgis.PyQt.QtCore import QMetaType
    _T_STRING = QMetaType.Type.QString
    _T_DOUBLE = QMetaType.Type.Double
    _T_INT = QMetaType.Type.Int

from . import priorityareas_vocabulary as vocab
from .priorityareas_config import (
    GROUP_NAME,
)

# Shared attribute schema. Order matters only for readability — features are
# written by field name, so the GeoPackage's automatic 'fid' column is safe.
ATTR_FIELDS = (
    "check_type",
    "habitat",
    "note",
    "lon",
    "lat",
    "created_at",
)


def build_fields():
    """The Priority Areas attribute schema as a QgsFields object."""
    fields = QgsFields()
    fields.append(QgsField("check_type", _T_STRING, len=40))
    fields.append(QgsField("habitat",    _T_STRING, len=40))
    fields.append(QgsField("note",       _T_STRING, len=500))
    fields.append(QgsField("lon",        _T_DOUBLE))
    fields.append(QgsField("lat",        _T_DOUBLE))
    fields.append(QgsField("created_at", _T_STRING, len=30))
    return fields


def apply_attrs(feature, values):
    """Assign a positional value list to a feature by field name."""
    for field_name, value in zip(ATTR_FIELDS, values):
        feature.setAttribute(field_name, value)


# ----------------------------------------------------------------------
# Enum compatibility (Qt5 / Qt6 builds)
# ----------------------------------------------------------------------

def _wkb_for(geom_type):
    # QGIS 4 / Qt6 prefers the Qgis.WkbType enum; fall back to the older
    # QgsWkbTypes forms for QGIS 3.
    try:
        table = {
            "point":   Qgis.WkbType.Point,
            "line":    Qgis.WkbType.LineString,
            "polygon": Qgis.WkbType.Polygon,
        }
    except AttributeError:
        try:
            table = {
                "point":   QgsWkbTypes.Type.Point,
                "line":    QgsWkbTypes.Type.LineString,
                "polygon": QgsWkbTypes.Type.Polygon,
            }
        except AttributeError:
            table = {
                "point":   QgsWkbTypes.Point,
                "line":    QgsWkbTypes.LineString,
                "polygon": QgsWkbTypes.Polygon,
            }
    return table[geom_type]


def _line_geometry_enum():
    # QGIS 4 returns Qgis.GeometryType.Line from layer.geometryType();
    # fall back to the deprecated QgsWkbTypes forms for QGIS 3.
    try:
        return Qgis.GeometryType.Line
    except AttributeError:
        try:
            return QgsWkbTypes.GeometryType.LineGeometry
        except AttributeError:
            return QgsWkbTypes.LineGeometry


# ----------------------------------------------------------------------
# GeoPackage creation / loading
# ----------------------------------------------------------------------

def _create_gpkg_layer(gpkg_path, layer_name, geom_type, crs):
    """Create an empty Priority Areas layer inside the GeoPackage."""
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    options.fileEncoding = "UTF-8"

    try:
        overwrite_file = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
        overwrite_layer = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
        no_error = QgsVectorFileWriter.WriterError.NoError
    except AttributeError:
        overwrite_file = QgsVectorFileWriter.CreateOrOverwriteFile
        overwrite_layer = QgsVectorFileWriter.CreateOrOverwriteLayer
        no_error = QgsVectorFileWriter.NoError

    options.actionOnExistingFile = (
        overwrite_layer if os.path.exists(gpkg_path) else overwrite_file
    )

    writer = QgsVectorFileWriter.create(
        gpkg_path,
        build_fields(),
        _wkb_for(geom_type),
        crs,
        QgsProject.instance().transformContext(),
        options,
    )
    err = writer.hasError()
    del writer   # flush + close file handle
    if err != no_error:
        raise RuntimeError(
            "Failed to create Priority Areas layer '{}' in the GeoPackage.".format(layer_name)
        )


def get_or_create_layer(layer_name, geom_type, group, project, gpkg_path):
    """
    Return the named Priority Areas layer, loading it from (or creating it in) the
    GeoPackage and adding it to the Priority Areas group. Styling is applied on
    first creation.
    """
    # Already in the group?
    for tree_layer in group.findLayers():
        lyr = tree_layer.layer()
        if lyr is not None and lyr.name() == layer_name:
            return lyr

    uri = "{}|layername={}".format(gpkg_path, layer_name)

    # Already on disk? Load it. Otherwise create it first.
    if not (os.path.exists(gpkg_path)
            and QgsVectorLayer(uri, layer_name, "ogr").isValid()):
        _create_gpkg_layer(gpkg_path, layer_name, geom_type, project.crs())

    layer = QgsVectorLayer(uri, layer_name, "ogr")
    if layer is None or not layer.isValid():
        raise RuntimeError("Failed to load Priority Areas layer '{}'.".format(layer_name))

    # Style whenever the layer is first brought into this project. If it was
    # already styled and saved in the project, we returned early above.
    apply_habitat_style(layer, geom_type)
    apply_label(layer)

    project.addMapLayer(layer, False)
    group.addLayer(layer)
    return layer


# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------

def _symbol_for(geom_type, color):
    """A single symbol tinted for one habitat class."""
    if geom_type == "point":
        sym = QgsMarkerSymbol.createSimple({
            "name":          "circle",
            "size":          "3.4",
            "outline_color": "#FFFFFF",
            "outline_width": "0.4",
        })
    elif geom_type == "line":
        sym = QgsLineSymbol.createSimple({
            "width":      "0.9",
            "line_style": "solid",
        })
    else:  # polygon — light fill so the habitat layer beneath stays visible
        sym = QgsFillSymbol.createSimple({
            "style":         "solid",
            "outline_style": "solid",
            "outline_width": "0.6",
        })
    sym.setColor(QColor(color))
    if geom_type == "polygon":
        # Semi-transparent fill, opaque outline.
        fill_color = QColor(color)
        fill_color.setAlpha(55)
        sym.setColor(fill_color)
        try:
            sym.symbolLayer(0).setStrokeColor(QColor(color))
        except AttributeError:
            pass
    return sym


def apply_habitat_style(layer, geom_type):
    """Categorized renderer keyed on 'habitat', coloured by the vocabulary."""
    habitats = vocab.habitats()
    colors = vocab.habitat_colors()
    categories = []
    for habitat in habitats:
        color = colors.get(habitat, "#888888")
        categories.append(
            QgsRendererCategory(habitat, _symbol_for(geom_type, color), habitat)
        )
    # Fallback category for anything without a recognised habitat.
    categories.append(
        QgsRendererCategory("", _symbol_for(geom_type, "#888888"), "Unset")
    )
    renderer = QgsCategorizedSymbolRenderer("habitat", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def apply_label(layer):
    """Label each feature with its check type; placement per geometry."""
    pal = QgsPalLayerSettings()
    pal.fieldName = (
        '"check_type" || '
        'if("note" IS NOT NULL AND "note" != \'\', \'\\n\' || "note", \'\')'
    )
    pal.isExpression = True
    pal.enabled = True

    text_format = QgsTextFormat()
    text_format.setColor(QColor("#111111"))
    text_format.setSize(8)

    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(1)
    buffer_settings.setColor(QColor("#FFFFFF"))
    text_format.setBuffer(buffer_settings)

    pal.setFormat(text_format)

    # Placement enum: Qgis.LabelPlacement in QGIS 4, unscoped form in QGIS 3.
    try:
        placement_line = Qgis.LabelPlacement.Line
        placement_around = Qgis.LabelPlacement.AroundPoint
    except AttributeError:
        placement_line = QgsPalLayerSettings.Line
        placement_around = QgsPalLayerSettings.AroundPoint

    if layer.geometryType() == _line_geometry_enum():
        pal.placement = placement_line
    else:
        pal.placement = placement_around

    labeling = QgsVectorLayerSimpleLabeling(pal)
    layer.setLabelsEnabled(True)
    layer.setLabeling(labeling)
    layer.triggerRepaint()


def _geom_key(layer):
    """Map a layer's geometry type to 'point' / 'line' / 'polygon'."""
    gt = layer.geometryType()
    try:
        if gt == Qgis.GeometryType.Point:
            return "point"
        if gt == Qgis.GeometryType.Line:
            return "line"
        if gt == Qgis.GeometryType.Polygon:
            return "polygon"
    except AttributeError:
        if gt == QgsWkbTypes.PointGeometry:
            return "point"
        if gt == QgsWkbTypes.LineGeometry:
            return "line"
        if gt == QgsWkbTypes.PolygonGeometry:
            return "polygon"
    return None


def restyle_project_layers(project=None):
    """Re-apply habitat styling + labels to Priority Areas layers already in
    the project, so vocabulary/colour changes show on existing annotations.

    Returns the number of layers restyled. Only touches styling — never data.
    """
    if project is None:
        project = QgsProject.instance()
    group = project.layerTreeRoot().findGroup(GROUP_NAME)
    if group is None:
        return 0
    count = 0
    for tree_layer in group.findLayers():
        layer = tree_layer.layer()
        if layer is None:
            continue
        geom = _geom_key(layer)
        if geom:
            apply_habitat_style(layer, geom)
            apply_label(layer)
            count += 1
    return count
