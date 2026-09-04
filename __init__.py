# -*- coding: utf-8 -*-
"""Priority Areas — desktop map annotation for planning field validation."""


def classFactory(iface):
    from .priorityareas_plugin import PriorityAreasPlugin
    return PriorityAreasPlugin(iface)
