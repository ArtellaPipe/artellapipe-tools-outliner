#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow to manage scene assets using Artella Pipeline
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
import inspect
import importlib
from functools import partial
from collections import OrderedDict

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import python
from tpDcc.libs.qt.core import qtutils, base
from tpDcc.libs.qt.widgets import stack, splitters

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import tpDcc

import artellapipe

# from artellapipe.utils import shader

LOGGER = logging.getLogger()


class ArtellaOutlinerSettings(base.BaseWidget, object):

    settingsSaved = Signal()

    def __init__(self, parent=None):
        super(ArtellaOutlinerSettings, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaOutlinerSettings, self).ui()

        self.save_btn = QPushButton('Save')
        self.save_btn.setIcon(tpDcc.ResourcesMgr().icon('save'))
        self.main_layout.addWidget(self.save_btn)

    def setup_signals(self):
        self.save_btn.clicked.connect(self.settingsSaved.emit)


class ArtellaOutlinerWidget(artellapipe.ToolWidget, object):
    def __init__(self, project, config, settings, parent=None):

        self._project = project
        self._config = config
        self._outliners = OrderedDict()
        self._registered_outliner_classes = OrderedDict()

        super(ArtellaOutlinerWidget, self).__init__(project=project, config=config, settings=settings, parent=parent)

        self._register_outliner_classes()
        self._create_outliners()
        self._init_outliners()

        self.update_categories()

    def ui(self):
        super(ArtellaOutlinerWidget, self).ui()

        self._toolbar = QToolBar()
        self._setup_toolbar()
        self.main_layout.addWidget(self._toolbar)

        self._main_stack = stack.SlidingStackedWidget(self)
        self.main_layout.addWidget(self._main_stack)

        self._outliner_widget = QWidget()
        self._outliner_layout = QVBoxLayout()
        self._outliner_layout.setContentsMargins(2, 2, 2, 2)
        self._outliner_layout.setSpacing(2)
        self._outliner_widget.setLayout(self._outliner_layout)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        top_layout.setAlignment(Qt.AlignCenter)

        self._tags_menu_layout = QHBoxLayout()
        self._tags_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_menu_layout.setSpacing(0)
        self._tags_menu_layout.setAlignment(Qt.AlignTop)
        top_layout.addLayout(self._tags_menu_layout)

        self._tags_btn_grp = QButtonGroup(self)
        self._tags_btn_grp.setExclusive(True)

        self._outliners_stack = stack.SlidingStackedWidget()
        self._outliner_layout.addLayout(top_layout)
        self._outliner_layout.addLayout(splitters.SplitterLayout())
        self._outliner_layout.addWidget(self._outliners_stack)

        self._settings_widget = ArtellaOutlinerSettings()

        self._main_stack.addWidget(self._outliner_widget)
        self._main_stack.addWidget(self._settings_widget)

        # self.settingswidget.settingsSaved.connect(self.open_tabs)

    def update_categories(self):
        """
        Updates current tag categories with the given ones
        """

        for btn in self._tags_btn_grp.buttons():
            self._tags_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._tags_menu_layout)

        if not self._outliners:
            return

        total_buttons = 0

        categories_list = self._outliners.keys()
        for category in categories_list:
            new_btn = QPushButton(category.title())
            new_btn.category = category
            category_icon = tpDcc.ResourcesMgr().icon(category.strip().lower())
            new_btn.setIcon(category_icon)
            new_btn.setCheckable(True)
            new_btn.clicked.connect(partial(self._on_change_outliner, new_btn))
            self._tags_menu_layout.addWidget(new_btn)
            self._tags_btn_grp.addButton(new_btn)
            if total_buttons == 0:
                new_btn.blockSignals(True)
                new_btn.setChecked(True)
                new_btn.blockSignals(False)
            total_buttons += 1

    def add_outliner(self, outliner_type, outliner_widget):
        """
        Adds a new outliner to the stack widget
        :param outliner_type: str
        :param outliner_widget: BaseOutliner
        """

        if outliner_type in self._outliners:
            LOGGER.warning('Outliner {} already exists!'.format(outliner_widget))
            return

        self._outliners[outliner_type] = outliner_widget
        self._outliners_stack.addWidget(outliner_widget)

    def _setup_toolbar(self):
        """
        Internal function that setup toolbar for outliner tool
        """

        low_resolution_action = QToolButton(self)
        low_resolution_action.setText('All Low')
        low_resolution_action.setToolTip('Enable High Resolution Mesh in all assets in current scene')
        low_resolution_action.setStatusTip('Enable High Resolution Mesh in all assets in current scene')
        low_resolution_action.setIcon(tpDcc.ResourcesMgr().icon('low_poly', key='tools'))
        low_resolution_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        high_resolution_action = QToolButton(self)
        high_resolution_action.setText('All High')
        high_resolution_action.setToolTip('Enable High Resolution Mesh in all assets in current scene')
        high_resolution_action.setStatusTip('Enable High Resolution Mesh in all assets in current scene')
        high_resolution_action.setIcon(tpDcc.ResourcesMgr().icon('high_poly'))
        high_resolution_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        load_scene_shaders_action = QToolButton(self)
        load_scene_shaders_action.setText('Load Shaders')
        load_scene_shaders_action.setToolTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setStatusTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setIcon(tpDcc.ResourcesMgr().icon('shading_load'))
        load_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        unload_scene_shaders_action = QToolButton(self)
        unload_scene_shaders_action.setText('Unload Shaders')
        unload_scene_shaders_action.setToolTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setStatusTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setIcon(tpDcc.ResourcesMgr().icon('shading_unload'))
        unload_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        update_refs_action = QToolButton(self)
        update_refs_action.setText('Sync Assets')
        update_refs_action.setToolTip('Updates all asset references to the latest published version')
        update_refs_action.setStatusTip('Updates all asset references to the latest published version')
        update_refs_action.setIcon(tpDcc.ResourcesMgr().icon('sync_cloud'))
        update_refs_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        export_overrides_action = QToolButton(self)
        export_overrides_action.setText('Save Overrides')
        export_overrides_action.setToolTip('Stores overrides into disk')
        export_overrides_action.setStatusTip('Stores overrides into disk')
        export_overrides_action.setIcon(tpDcc.ResourcesMgr().icon('save'))
        export_overrides_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        settings_action = QToolButton(self)
        settings_action.setText('Settings')
        settings_action.setToolTip('Outliner Settings')
        settings_action.setStatusTip('Outliner Settings')
        settings_action.setIcon(tpDcc.ResourcesMgr().icon('settings'))
        settings_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self._toolbar.addWidget(low_resolution_action)
        self._toolbar.addWidget(high_resolution_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(load_scene_shaders_action)
        self._toolbar.addWidget(unload_scene_shaders_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(update_refs_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(export_overrides_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(settings_action)

        low_resolution_action.clicked.connect(self._on_lowres_assets)
        high_resolution_action.clicked.connect(self._on_hires_assets)
        load_scene_shaders_action.clicked.connect(self._on_load_scene_shaders)
        unload_scene_shaders_action.clicked.connect(self._on_unload_scene_shaders)
        # settings_action.clicked.connect(self.open_settings)

    def register_outliner_class(self, outliner_type, outliner_class):
        """
        Registers a new outliner class
        :param outliner_type: str
        :param outliner_class: class
        """

        self._registered_outliner_classes[outliner_type] = outliner_class
        return True

    def select_asset(self, *args, **kwargs):
        current_outliner = self._outliners_stack.currentWidget()
        if not current_outliner:
            return

        selected_nodes = tp.Dcc.selected_nodes()
        if not selected_nodes:
            current_outliner.clear_selection()
            return

        selected_node = selected_nodes[0]
        node_namespace = tp.Dcc.node_namespace(selected_node)
        if not node_namespace:
            return

        if node_namespace.startswith('|') or node_namespace.startswith(':'):
            node_namespace = node_namespace[1:]

        current_outliner.select_item(node_namespace)

    def _create_outliners(self):
        """
        Internal function that creates the outliner widgets
        """

        if not self._registered_outliner_classes:
            LOGGER.warning('No registered outliner classes found!')
            return

        for outliner_type, outliner_class in reversed(self._registered_outliner_classes.items()):
            new_outliner = outliner_class(project=self._project)
            self.add_outliner(outliner_type, new_outliner)

    def _init_outliners(self):
        """
        Internal function that initializes current outliners
        """

        for outliner in self._outliners.values():
            outliner.refresh()

    def _on_lowres_assets(self):
        """
        Internal function that is called when Low Res Assets menubar button is pressed
        """

        scene_assets = artellapipe.AssetsMgr().get_scene_assets()
        if not scene_assets:
            return

        for scene_asset in scene_assets:
            scene_asset.switch_to_proxy()

    def _on_hires_assets(self):
        """
        Internal function that is called when High Res Assets menubar button is pressed
        """

        scene_assets = artellapipe.AssetsMgr().get_scene_assets()
        if not scene_assets:
            return

        for scene_asset in scene_assets:
            scene_asset.switch_to_hires()

    def _on_load_scene_shaders(self):
        """
        Internal callback function that is called when Load Scene Shaders menubar button is pressed
        """

        artellapipe.ShadersMgr().load_scene_shaders()

    def _on_unload_scene_shaders(self):
        """
        Internal callback function that is called when Unload Scene Shaders menubar button is pressed
        """

        artellapipe.ShadersMgr().unload_shaders()

    def _on_change_outliner(self, toggled_btn):
        """
        Internal callback function that is called each time outliner category button is pressed
        :param toggled_btn: QPushButon, button toggled
        """

        for btn in self._tags_btn_grp.buttons():
            if btn == toggled_btn:
                selected_category = toggled_btn.text()
                for outliner in self._outliners.values():
                    if outliner.NAME == selected_category:
                        outliner_index = self._outliners_stack.indexOf(outliner)
                        self._outliners_stack.slide_in_index(outliner_index)
                        break

    def _register_outliner_classes(self):
        """
        Internal function that registers outliner classes
        """

        if not self._project:
            LOGGER.warning('Impossible to register outliner classes because Artella project is not defined!')
            return False

        outliners_data = self._config.get('outliners', default=dict())
        if not outliners_data:
            LOGGER.warning('No outliners found in artellapipe-tools-outliner configuration file to register!')
            return

        for outliner_type, outliner_info in outliners_data.items():
            full_outliner_class = outliner_info.get('class', None)
            if not full_outliner_class:
                LOGGER.warning('No class defined for Outliner Type "{}". Skipping ...'.format(outliner_type))
                continue
            outliner_class_split = full_outliner_class.split('.')
            outliner_class = outliner_class_split[-1]
            outliner_name = outliner_info.get('name', outliner_class)
            outliner_categories = outliner_info.get('categories', list())
            outliner_module = '.'.join(outliner_class_split[:-1])
            LOGGER.info('Registering Outliner: {}'.format(outliner_module))

            try:
                module_loader = loader.find_loader(outliner_module)
            except Exception as exc:
                LOGGER.warning('Impossible to register Outliner Module: {} | {}'.format(outliner_module, exc))
                continue
            if not module_loader:
                LOGGER.warning('Impossible to load Outliner Module: {}'.format(outliner_module))
                continue

            class_found = None
            try:
                mod = importlib.import_module(module_loader.fullname)
            except Exception as exc:
                LOGGER.warning('Impossible to register outliner class: {} | {}'.format(module_loader.fullname, exc))
                continue

            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if cname == outliner_class:
                    class_found = obj
                    break

            if not class_found:
                LOGGER.warning('No Outliner Class "{}" found in Module: "{}"'.format(outliner_class, outliner_module))
                continue

            obj.NAME = outliner_name
            obj.CATEGORIES = outliner_categories

            self.register_outliner_class(outliner_type, obj)

        return True
