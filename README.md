# Priority Areas

A QGIS plugin for **annotating a map before fieldwork** — flagging the points, lines and areas the field team needs to look at, so ground-truthing effort goes where it matters.

Priority Areas sits *upstream* of field data capture. The desktop mapper marks up predicted habitat with quick, structured annotations (a habitat class and a check type — "check boundary", "confirm classification", "possible dieback", and so on); those annotations then travel with the project into the field, where a separate validation tool records what's actually there.

- **Works on QGIS 3.16+ and QGIS 4.x** (Qt5 and Qt6)
- **Licence:** GPL-3.0-or-later

---

## What it does

- Three toolbar tools — **point**, **line**, **area** — for flagging spots, boundaries/transects, and priority polygons.
- After you draw, a short dialog captures a **habitat class**, a **check type**, and an optional **note**.
- Annotations are **coloured by habitat** so the map reads at a glance, and **labelled by check type** (with the note appended underneath when there is one).
- Everything is written to a **GeoPackage in the project folder** (`PriorityAreas.gpkg`), grouped under a `Priority Areas` layer group — so it's saved, portable, and opens with the project.
- The whole vocabulary — habitat classes, their colours, and the check types — is **driven by one config file** you can edit without touching the plugin logic.

---

## Requirements

- QGIS **3.16 or newer**, including the QGIS **4.x** series.
- No external Python dependencies.

---

## Installation

### From ZIP (easiest)

1. Download the repository as a ZIP, or grab a release ZIP.
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**, choose the file, and install.
3. Enable **Priority Areas** in the plugin list if it isn't already.

### From source

Clone directly into your QGIS profile's plugin folder:

```bash
git clone https://github.com/GregjWest/QGIS_PriorityAreas.git
```

Place the folder in your profile's `python/plugins` directory:

- **Windows:** `C:\Users\<you>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
  (for QGIS 4, `...\QGIS\QGIS4\profiles\default\python\plugins\`)
- **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
- **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

Then restart QGIS (or use the *Plugin Reloader* plugin during development) and enable it.

---

## Usage

1. **Save your QGIS project first.** Annotations are stored alongside the project file, so the project needs a home on disk. If it isn't saved, the plugin tells you and skips the mark.
2. Pick a tool from the **Priority Areas** toolbar — point, line or area.
3. **Draw:**
   - *Point* — click once.
   - *Line / area* — click to add vertices; **double-click or right-click to finish**. The draft polygon is drawn semi-transparent so you can see the habitat underneath while you trace.
4. In the dialog, choose the **habitat**, the **check type**, and add a **note** if useful, then **Add annotation**.
5. The feature is written to `PriorityAreas.gpkg` and styled automatically. Your last habitat/check-type choices are remembered for the next annotation, so a run of similar flags is quick.

---

## Configuration

All of the tool's vocabulary lives in **`priorityareas_config.py`**. Edit the lists and dictionaries there — no other code changes needed — and the dialog, the stored values and the map legend all follow.

```python
# Habitat classes shown in the dialog, in order.
HABITATS = [
    "Posidonia",
    "Zostera",
    "Mangrove",
    "Saltmarsh",
    "Seagrass",
    "Other",
]

# The colour each habitat draws with on the map.
HABITAT_COLORS = {
    "Posidonia": "#ff0080",
    "Zostera":   "#0BF5FD",
    "Mangrove":  "#13DF00",
    "Saltmarsh": "#FFBD17",
    "Seagrass":  "#00ACC1",
    "Other":     "#8C00FF",
}

# What the field team needs to look at. Used as the map label.
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
```

**To add a habitat:** add it to `HABITATS` *and* give it a colour in `HABITAT_COLORS`.
**To change a colour:** edit its hex value in `HABITAT_COLORS`.
**To change the check-type list:** edit `CHECK_TYPES`.

The same file also sets the default selections and the storage names (`GPKG_NAME`, `GROUP_NAME`, and the per-geometry layer names).

> Colours apply to newly created layers. If you change a colour after a layer already exists, re-apply the style (or start a fresh GeoPackage) to see it.

### Toolbar icons

The three tools use `resources/icon_point`, `icon_line`, and `icon_polygon` (PNG preferred, then SVG), falling back to the generic icon. Drop in your own files with those names to restyle the toolbar — no code change needed.

---

## Data model

Each annotation carries:

| Field | Description |
|-------|-------------|
| `check_type` | What to look at (drives the label) |
| `habitat` | Habitat class (drives the colour) |
| `note` | Free-text note for the field team |
| `lon`, `lat` | Representative point in WGS84, for reference |
| `created_at` | Timestamp |

Points, lines and polygons are stored as three separate layers (`POINTS`, `LINES`, `POLYGONS`) inside the one GeoPackage.

---

## Notes and limitations

- The project must be saved before annotations can be stored (see Usage).
- Styling and labelling are applied when a layer is first created in a project and then saved in the project file; existing GeoPackages picked up in a fresh project are re-styled on load.
- This tool is for **planning** the fieldwork — it captures *what to check*, not the validation observations themselves.

---

## Licence

Released under the **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE) for the full text.

---

## Acknowledgements

Built for coastal habitat mapping and estuarine field-validation planning (seagrass, mangrove and saltmarsh). The plugin structure and map-tool approach were informed by the open-source [GeoMark](https://github.com/erlrich/GeoMark) annotation plugin.
