#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that manage the assets in a DCC scene
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import artellapipe

# Defines ID of the tool
TOOL_ID = 'artellapipe-tools-outliner'

# We skip the reloading of this module when launching the tool
no_reload = True


class OutlinerTool(artellapipe.Tool, object):
    def __init__(self, *args, **kwargs):
        super(OutlinerTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = artellapipe.Tool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Outliner', 'id': 'artellapipe-tools-outliner',
            'logo': 'outliner_logo',
            'icon': 'modelchecker',
            'tooltip': 'Tool that manage the assets in a DCC scene',
            'tags': ['outliner', 'asset'],
            'sentry_id': 'https://f489c1a2f43c4c629ba6f08f6c3ef727@sentry.io/1764485',
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {
                'label': 'Outliner', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [
                {'label': 'General',
                 'type': 'menu', 'children': [{'id': 'artellapipe-tools-outliner', 'type': 'tool'}]}],
            'shelf': [
                {'name': 'General',
                 'children': [{'id': 'artellapipe-tools-outliner', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config


class OutlinerToolset(artellapipe.Toolset, object):
    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(OutlinerToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from artellapipe.tools.outliner.widgets import outliner

        outliner_widget = outliner.ArtellaOutlinerWidget(
            project=self._project, config=self._config, settings=self._settings, parent=self)
        return [outliner_widget]
