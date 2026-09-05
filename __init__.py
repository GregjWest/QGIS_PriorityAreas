# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Greg West
"""Priority Areas — desktop map annotation for planning field validation."""


def classFactory(iface):
    from .priorityareas_plugin import PriorityAreasPlugin
    return PriorityAreasPlugin(iface)
