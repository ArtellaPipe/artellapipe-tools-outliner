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

import weakref
import logging.config
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import qtutils, base
from tpQtLib.widgets import stack, splitters

from artellapipe.utils import resource
from artellapipe.core import tool

# from artellapipe.utils import shader

LOGGER = logging.getLogger()


class ArtellaOutlinerSettings(base.BaseWidget, object):

    settingsSaved = Signal()

    def __init__(self, parent=None):
        super(ArtellaOutlinerSettings, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaOutlinerSettings, self).ui()

        self.save_btn = QPushButton('Save')
        self.save_btn.setIcon(resource.ResourceManager().icon('save'))
        self.main_layout.addWidget(self.save_btn)

    def setup_signals(self):
        self.save_btn.clicked.connect(self.settingsSaved.emit)


class ArtellaOutlinerWidget(QWidget, object):

    # Necessary to support Maya dock
    name = 'ArtellaOutlinerWidget'
    title = 'Artella Outliner'

    _instances = list()

    def __init__(self, project, parent=None):

        self._project = project
        self._outliners = list()

        main_window = tp.Dcc.get_main_window()
        if parent is None:
            parent = main_window

        super(ArtellaOutlinerWidget, self).__init__(parent=parent)

        if tp.is_maya():
            ArtellaOutlinerWidget._delete_instances()
            self.__class__._instances.append(weakref.proxy(self))

        self.ui()
        self._create_outliners()
        self._init_outliners()

    @staticmethod
    def _delete_instances():
        for ins in ArtellaOutlinerWidget._instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except Exception:
                pass

            ArtellaOutlinerWidget._instances.remove(ins)
            del ins

    def ui(self):

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # if tp.is_maya():
        #     self.parent().layout().addLayout(self.main_layout)
        # else:
        #     self.setLayout(self.main_layout)

        self.setLayout(self.main_layout)

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
        outliner_categories = self._project.outliner_categories.keys() if self._project else list()

        self._outliners_stack = stack.SlidingStackedWidget()
        self._outliner_layout.addLayout(top_layout)
        self._outliner_layout.addLayout(splitters.SplitterLayout())
        self._outliner_layout.addWidget(self._outliners_stack)

        self._settings_widget = ArtellaOutlinerSettings()

        self._main_stack.addWidget(self._outliner_widget)
        self._main_stack.addWidget(self._settings_widget)

        self.update_categories(outliner_categories)

        # self.settingswidget.settingsSaved.connect(self.open_tabs)

    def update_categories(self, outliner_categories):
        """
        Updates current tag categories with the given ones
        :param outliner_categories: list(str)
        """

        for btn in self._tags_btn_grp.buttons():
            self._tags_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._tags_menu_layout)

        total_buttons = 0
        for category in reversed(outliner_categories):
            new_btn = QPushButton(category.title())
            new_btn.category = category
            category_icon = resource.ResourceManager().icon(category.strip().lower())
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

    def add_outliner(self, outliner_widget):
        """
        Adds a new outliner to the stack widget
        :param outliner_widget: BaseOutliner
        """

        if outliner_widget in self._outliners:
            LOGGER.warning('Outliner {} already exists!'.format(outliner_widget))
            return

        self._outliners.append(outliner_widget)
        self._outliners_stack.addWidget(outliner_widget)

    def _setup_toolbar(self):
        load_scene_shaders_action = QToolButton(self)
        load_scene_shaders_action.setText('Load Shaders')
        load_scene_shaders_action.setToolTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setStatusTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setIcon(resource.ResourceManager().icon('shading_load'))
        load_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        unload_scene_shaders_action = QToolButton(self)
        unload_scene_shaders_action.setText('Unload Shaders')
        unload_scene_shaders_action.setToolTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setStatusTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setIcon(resource.ResourceManager().icon('shading_unload'))
        unload_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        update_refs_action = QToolButton(self)
        update_refs_action.setText('Sync Assets')
        update_refs_action.setToolTip('Updates all asset references to the latest published version')
        update_refs_action.setStatusTip('Updates all asset references to the latest published version')
        update_refs_action.setIcon(resource.ResourceManager().icon('sync_cloud'))
        update_refs_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        export_overrides_action = QToolButton(self)
        export_overrides_action.setText('Save Overrides')
        export_overrides_action.setToolTip('Stores overrides into disk')
        export_overrides_action.setStatusTip('Stores overrides into disk')
        export_overrides_action.setIcon(resource.ResourceManager().icon('save'))
        export_overrides_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        settings_action = QToolButton(self)
        settings_action.setText('Settings')
        settings_action.setToolTip('Outliner Settings')
        settings_action.setStatusTip('Outliner Settings')
        settings_action.setIcon(resource.ResourceManager().icon('settings'))
        settings_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self._toolbar.addWidget(load_scene_shaders_action)
        self._toolbar.addWidget(unload_scene_shaders_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(update_refs_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(export_overrides_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(settings_action)

        load_scene_shaders_action.clicked.connect(self._on_load_scene_shaders)
        unload_scene_shaders_action.clicked.connect(self._on_unload_scene_shaders)
        # settings_action.clicked.connect(self.open_settings)

    def _create_outliners(self):
        """
        Internal function that creates the outliner widgets
        """

        pass

    def _init_outliners(self):
        """
        Internal function that initializes current outliners
        """

        for outliner in self._outliners:
            outliner.refresh()

    def _on_load_scene_shaders(self):
        """
        Internal callback function that is called when Load Scene Shaders menubar button is pressed
        """

        LOGGER.warning('Load Shaders functionality not available!')
        # shader.load_scene_shaders(project=self._project)

    def _on_unload_scene_shaders(self):
        """
        Internal callback function that is called when Unload Scene Shaders menubar button is pressed
        """

        LOGGER.warning('Unload Shaders functionality not available')
        # shader.unload_shaders(project=self._project)

    def _on_change_outliner(self, toggled_btn):
        """
        Internal callback function that is called each time outliner category button is pressed
        :param toggled_btn: QPushButon, button toggled
        """

        for btn in self._tags_btn_grp.buttons():
            if btn == toggled_btn:
                selected_category = toggled_btn.text()
                for outliner in self._outliners:
                    if outliner.OUTLINER_NAME == selected_category:
                        outliner_index = self._outliners_stack.indexOf(outliner)
                        self._outliners_stack.slide_in_index(outliner_index)


class ArtellaOutliner(tool.Tool, object):

    def __init__(self, project, config):
        super(ArtellaOutliner, self).__init__(project=project, config=config)

    def ui(self):
        super(ArtellaOutliner, self).ui()

        self._outliner = ArtellaOutlinerWidget(project=self._project)
        self.main_layout.addWidget(self._outliner)


# def run(project):
#     if tp.is_maya():
#         win = window.dock_window(project=project, window_class=ArtellaOutlinerWidget)
#         return win
#     else:
#         win = ArtellaOutliner(project=project)
#         win.show()
#         return win