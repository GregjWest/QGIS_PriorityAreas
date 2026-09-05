# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project aims to follow
[Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-09-05

First public release.

### Added
- Point, line and area annotation tools on a **Priority Areas** toolbar.
- Annotation dialog capturing a **habitat class**, a **check type**, and an optional **note**.
- Habitat-driven categorized styling, with the check type shown as the label and the note appended when present.
- Storage in a **GeoPackage in the project folder** (`PriorityAreas.gpkg`), with point/line/polygon layers under a `Priority Areas` group.
- Config-driven vocabulary — habitats, colours and check types are edited in `priorityareas_config.py`.
- Per-geometry toolbar icons with drop-in override from `resources/`.
- Semi-transparent draft polygon while drawing, so underlying habitat stays visible.
- **QGIS 3.16+ and QGIS 4.x (Qt5/Qt6) support**, including scoped-enum and field-type handling for Qt6, and `qgisMaximumVersion=4.99` so the plugin loads under QGIS 4.
- Project documentation: README, GPL-3.0-or-later licensing and per-file SPDX headers.

[0.5.0]: https://github.com/GregjWest/QGIS_PriorityAreas/releases/tag/v0.5.0
