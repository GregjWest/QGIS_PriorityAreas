# -*- coding: utf-8 -*-
"""
Priority Areas map tool.

Handles canvas drawing for point / line / polygon annotations (left-click to
place vertices, right-click or double-click to finish lines and polygons),
then opens the Priority Areas dialog and writes the feature to the project's
GeoPackage. Event handling mirrors GeoMark's well-tested approach.
"""

import os
from datetime import datetime

from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import (
    QgsProject,
    Qgis,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog

from .priorityareas_config import (
    GROUP_NAME,
    GPKG_NAME,
    LAYER_POINT,
    LAYER_LINE,
    LAYER_POLY,
    DEFAULT_CHECK_TYPE,
    DEFAULT_HABITAT,
)
from .priorityareas_layers import get_or_create_layer, apply_attrs
from .priorityareas_dialog import PriorityAreasDialog

# Qt5 / Qt6 enum compatibility
try:
    QT_LEFT_BUTTON = Qt.MouseButton.LeftButton
    QT_RIGHT_BUTTON = Qt.MouseButton.RightButton
except AttributeError:
    QT_LEFT_BUTTON = Qt.LeftButton
    QT_RIGHT_BUTTON = Qt.RightButton

# Geometry-type enum for the rubber band: Qgis.GeometryType in QGIS 4,
# older QgsWkbTypes forms in QGIS 3.
try:
    _POLY_GEOM = Qgis.GeometryType.Polygon
    _LINE_GEOM = Qgis.GeometryType.Line
except AttributeError:
    try:
        _POLY_GEOM = QgsWkbTypes.GeometryType.PolygonGeometry
        _LINE_GEOM = QgsWkbTypes.GeometryType.LineGeometry
    except AttributeError:
        _POLY_GEOM = QgsWkbTypes.PolygonGeometry
        _LINE_GEOM = QgsWkbTypes.LineGeometry

try:
    _DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
except AttributeError:
    _DIALOG_ACCEPTED = QDialog.Accepted

_PREVIEW_COLOR = QColor("#1565C0")


class PriorityAreasMapTool(QgsMapTool):
    """Draw Priority Areas annotations and persist them to the project GeoPackage."""

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)

        self._mode = None          # 'point' | 'line' | 'polygon'
        self._vertices = []
        self._rubber_band = None

        # Remembered so the mapper doesn't re-pick for every flag.
        self._defaults = {
            "check_type": DEFAULT_CHECK_TYPE,
            "habitat":    DEFAULT_HABITAT,
        }

    # ------------------------------------------------------------------
    # Mode
    # ------------------------------------------------------------------

    def set_mode(self, mode):
        """Set the geometry mode and reset any in-progress drawing."""
        self._mode = mode
        self._vertices = []
        self._clear_rubber_band()
        hints = {
            "point":   "Click on the map to place a Priority Areas point.",
            "line":    "Click to add vertices. Double-click or right-click to finish.",
            "polygon": "Click to add vertices. Double-click or right-click to finish (auto-closes).",
        }
        self.iface.statusBarIface().showMessage(hints.get(mode, ""))

    # ------------------------------------------------------------------
    # Canvas events
    # ------------------------------------------------------------------

    def canvasPressEvent(self, event):
        if self._mode is None:
            return

        if event.button() == QT_RIGHT_BUTTON:
            if self._mode in ("line", "polygon"):
                self._finish_line_polygon()
            return

        if event.button() != QT_LEFT_BUTTON:
            return

        map_point = self.toMapCoordinates(event.pos())

        if self._mode == "point":
            self._persist("point", QgsGeometry.fromPointXY(QgsPointXY(map_point)))
        else:
            self._vertices.append(QgsPointXY(map_point))
            self._update_rubber_band(self._vertices)

    def canvasDoubleClickEvent(self, event):
        if self._mode in ("line", "polygon"):
            # Drop the extra vertex the preceding single click just added.
            if self._vertices:
                self._vertices.pop()
            self._finish_line_polygon()

    def canvasMoveEvent(self, event):
        if self._mode not in ("line", "polygon") or not self._vertices:
            return
        map_point = self.toMapCoordinates(event.pos())
        self._update_rubber_band(self._vertices + [QgsPointXY(map_point)])

    def deactivate(self):
        self._clear_rubber_band()
        self._vertices = []
        self._mode = None
        super().deactivate()

    # ------------------------------------------------------------------
    # Rubber band preview
    # ------------------------------------------------------------------

    def _update_rubber_band(self, points):
        geom_kind = _POLY_GEOM if self._mode == "polygon" else _LINE_GEOM
        if self._rubber_band is None:
            self._rubber_band = QgsRubberBand(self.canvas, geom_kind)
            self._rubber_band.setWidth(2)
            if self._mode == "polygon":
                # Semi-transparent fill so the habitat layer stays visible
                # while marking; solid outline to show the shape clearly.
                fill = QColor(_PREVIEW_COLOR)
                fill.setAlpha(45)
                self._rubber_band.setFillColor(fill)
                self._rubber_band.setStrokeColor(QColor(_PREVIEW_COLOR))
            else:
                self._rubber_band.setColor(QColor(_PREVIEW_COLOR))
        self._rubber_band.reset(geom_kind)
        if self._mode == "polygon":
            geom = QgsGeometry.fromPolygonXY([points])
        else:
            geom = QgsGeometry.fromPolylineXY(points)
        self._rubber_band.setToGeometry(geom, None)

    def _clear_rubber_band(self):
        if self._rubber_band is not None:
            self.canvas.scene().removeItem(self._rubber_band)
            self._rubber_band = None

    # ------------------------------------------------------------------
    # Finish line / polygon
    # ------------------------------------------------------------------

    def _finish_line_polygon(self):
        pts = list(self._vertices)
        self._vertices = []
        self._clear_rubber_band()

        if self._mode == "line":
            if len(pts) < 2:
                self.iface.messageBar().pushInfo(
                    "Priority Areas", "A line needs at least two vertices."
                )
                return
            geom = QgsGeometry.fromPolylineXY(pts)
            self._persist("line", geom)
        else:  # polygon
            if len(pts) < 3:
                self.iface.messageBar().pushInfo(
                    "Priority Areas", "A polygon needs at least three vertices."
                )
                return
            geom = QgsGeometry.fromPolygonXY([pts])   # OGR closes the ring
            self._persist("polygon", geom)

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------

    def _persist(self, geom_type, geometry):
        project = QgsProject.instance()
        gpkg_path = self._resolve_gpkg_path()
        if gpkg_path is None:
            return

        geom_label = {"point": "Point", "line": "Line", "polygon": "Polygon"}[geom_type]
        dlg = PriorityAreasDialog(geom_label, self._defaults, self.iface.mainWindow())
        if dlg.exec() != _DIALOG_ACCEPTED:
            return

        vals = dlg.values()
        # Remember for the next annotation.
        for key in ("check_type", "habitat"):
            self._defaults[key] = vals[key]

        group = self._get_or_create_group()
        layer_name = {
            "point": LAYER_POINT, "line": LAYER_LINE, "polygon": LAYER_POLY
        }[geom_type]

        try:
            layer = get_or_create_layer(
                layer_name, geom_type, group, project, gpkg_path
            )
        except RuntimeError as exc:
            self.iface.messageBar().pushCritical("Priority Areas", str(exc))
            return

        lon, lat = self._lonlat(geometry, project)

        feat = QgsFeature(layer.fields())
        feat.setGeometry(geometry)
        apply_attrs(feat, [
            vals["check_type"],
            vals["habitat"],
            vals["note"],
            lon,
            lat,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

        ok, _ = layer.dataProvider().addFeatures([feat])
        layer.updateExtents()
        layer.triggerRepaint()
        self.canvas.refresh()

        if ok:
            self.iface.messageBar().pushSuccess(
                "Priority Areas",
                "{} · {} added.".format(vals["habitat"], vals["check_type"]),
            )
        else:
            self.iface.messageBar().pushWarning(
                "Priority Areas",
                "Could not write the annotation to the GeoPackage.",
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_gpkg_path(self):
        folder = QgsProject.instance().homePath()
        if not folder:
            self.iface.messageBar().pushWarning(
                "Priority Areas",
                "Save your QGIS project first — annotations are stored in "
                "'{}' next to the project file.".format(GPKG_NAME),
            )
            return None
        return os.path.join(folder, GPKG_NAME)

    def _get_or_create_group(self):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(GROUP_NAME)
        if group is None:
            group = root.insertGroup(0, GROUP_NAME)
        return group

    def _lonlat(self, geometry, project):
        """Representative point of the geometry in WGS84, for reference."""
        try:
            pt = geometry.centroid().asPoint()
            src = project.crs()
            dst = QgsCoordinateReferenceSystem("EPSG:4326")
            if src.isValid() and src != dst:
                xform = QgsCoordinateTransform(src, dst, project)
                pt = xform.transform(pt)
            return float(pt.x()), float(pt.y())
        except Exception:
            return None, None
