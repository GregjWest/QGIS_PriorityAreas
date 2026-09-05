# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""
Vocabulary store for Priority Areas.

The habitats (name + colour) and check types the user works with are held in a
JSON settings file in the active QGIS profile, seeded on first run from the
defaults in priorityareas_config.py. The rest of the plugin reads the current
vocabulary through the helpers here, so changes made in the Settings dialog (or
by hand-editing the JSON) take effect on the next annotation without touching
any .py file.

File location: <QGIS profile>/PriorityAreas/vocabulary.json
"""

import os
import json

from qgis.core import QgsApplication

from .priorityareas_config import HABITATS, HABITAT_COLORS, CHECK_TYPES

_FALLBACK_COLOR = "#888888"


def _settings_dir():
    base = QgsApplication.qgisSettingsDirPath()
    path = os.path.join(base, "PriorityAreas")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path


def settings_path():
    """Full path to the vocabulary JSON file."""
    return os.path.join(_settings_dir(), "vocabulary.json")


def defaults():
    """A fresh copy of the default vocabulary, from the config module."""
    return {
        "habitats": [
            {"name": name, "color": HABITAT_COLORS.get(name, _FALLBACK_COLOR)}
            for name in HABITATS
        ],
        "check_types": list(CHECK_TYPES),
    }


def _valid(data):
    return (
        isinstance(data, dict)
        and isinstance(data.get("habitats"), list) and data["habitats"]
        and isinstance(data.get("check_types"), list) and data["check_types"]
    )


def load():
    """Return the current vocabulary dict, seeding the file on first run."""
    path = settings_path()
    if not os.path.exists(path):
        data = defaults()
        save(data)          # write a config file the user can hand-edit
        return data
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return defaults()

    if not _valid(data):
        return defaults()

    # Normalise habitat entries (tolerate missing colours / stray keys).
    habitats = []
    for entry in data["habitats"]:
        if isinstance(entry, dict) and entry.get("name"):
            habitats.append({
                "name": str(entry["name"]),
                "color": str(entry.get("color", _FALLBACK_COLOR)),
            })
    checks = [str(c) for c in data["check_types"] if str(c).strip()]
    if not habitats or not checks:
        return defaults()
    return {"habitats": habitats, "check_types": checks}


def save(data):
    """Write the vocabulary dict to the settings file. Returns True on success."""
    try:
        with open(settings_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def reset():
    """Restore and persist the default vocabulary."""
    data = defaults()
    save(data)
    return data


# --- convenience accessors used across the plugin -------------------------

def habitats():
    return [h["name"] for h in load()["habitats"]]


def habitat_colors():
    return {h["name"]: h.get("color", _FALLBACK_COLOR) for h in load()["habitats"]}


def check_types():
    return list(load()["check_types"])


def default_habitat():
    names = habitats()
    return names[0] if names else ""


def default_check_type():
    checks = check_types()
    return checks[0] if checks else ""
