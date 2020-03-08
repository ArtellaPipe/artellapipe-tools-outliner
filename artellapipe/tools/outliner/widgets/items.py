#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains outliner item core widgets for Artella Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import decorators
from tpDcc.libs.qt.widgets import splitters

from artellapipe.tools.outliner.core import outlineritems, buttons
# from artellapipe.tools.shotmanager.apps import shotassembler

if tp.is_maya():
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    undo_decorator = maya_decorators.undo_chunk
else:
    undo_decorator = decorators.empty_decorator

LOGGER = logging.getLogger()


class OutlinerAssetItem(outlineritems.OutlinerItem, object):

    DISPLAY_BUTTONS = buttons.AssetDisplayButtons

    viewToggled = Signal(object)
    viewSolo = Signal(object, bool)

    def __init__(self, asset_node, parent=None):
        super(OutlinerAssetItem, self).__init__(asset_node=asset_node, parent=parent)

    def get_display_widget(self):
        return buttons.AssetDisplayButtons()

    def setup_signals(self):
        super(OutlinerAssetItem, self).setup_signals()

        if self._display_buttons:
            self._display_buttons.view_btn.clicked.connect(partial(self.viewToggled.emit, self))

    def add_asset_attributes_change_callback(self):
        pass
        # obj = self.asset.get_mobject()
        # vis_callback = OpenMaya.MNodeMessage.addAttributeChangedCallback(obj, partial(self._update_asset_attributes))
        # return vis_callback

    def _update_asset_attributes(self, msg, plug, otherplug, *client_data):
        pass

        # if self.block_callbacks is False:
        #     if msg & OpenMaya.MNodeMessage.kAttributeSet:
        #         if 'visibility' in plug.name():
        #             self.asset_buttons.view_btn.setChecked(plug.asBool())
        #         elif 'type' in plug.name():
        #             model_widget = self.get_file_widget(category='model')
        #             if model_widget is None:
        #                 artellapipe.logger.warning(
        #                 'Impossible to update type attribute because model wigdet is available!')
        #                 return
        #             model_widget.model_buttons.proxy_hires_cbx.setCurrentIndex(plug.asInt())


class OutlinerOverrideItem(outlineritems.OutlinerTreeItemWidget, object):

    removed = Signal()

    def __init__(self, override, parent=None):

        self._override = override

        super(OutlinerOverrideItem, self).__init__(name=override.OVERRIDE_NAME, parent=parent)

    def ui(self):
        super(OutlinerOverrideItem, self).ui()

        self.setMouseTracking(True)

        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.setStyleSheet('background-color: rgb(45,45,45);')

        icon_lbl = QLabel()
        icon_lbl.setMaximumWidth(18)
        icon_lbl.setPixmap(self._override.OVERRIDE_ICON.pixmap(self._override.OVERRIDE_ICON.actualSize(QSize(20, 20))))
        self._target_lbl = QLabel(self._name.title())
        self._editor_btn = QPushButton('Editor')
        self._editor_btn.setFlat(True)
        self._save_btn = QPushButton()
        self._editor_btn.setIcon(tp.ResourcesMgr().icon('editor'))
        self._save_btn.setFlat(True)
        self._save_btn.setIcon(tp.ResourcesMgr().icon('save'))
        self._delete_btn = QPushButton()
        self._delete_btn.setFlat(True)
        self._delete_btn.setIcon(tp.ResourcesMgr().icon('delete'))

        self._item_layout.addWidget(icon_lbl, 0, 1, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 2, 1, 1)
        self._item_layout.addWidget(self._target_lbl, 0, 3, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 4, 1, 1)
        self._item_layout.addWidget(self._editor_btn, 0, 5, 1, 1)
        self._item_layout.setColumnStretch(6, 7)
        self._item_layout.addWidget(self._save_btn, 0, 8, 1, 1)
        self._item_layout.addWidget(self._delete_btn, 0, 9, 1, 1)

    def setup_signals(self):
        self._editor_btn.clicked.connect(self._on_open_override_editor)
        self._save_btn.clicked.connect(self._on_save_override)
        self._delete_btn.clicked.connect(self._on_remove_override)

    def _on_open_override_editor(self):
        """
        Internal callback function that is called when Editor button is pressed
        """

        self._override.show_editor()

    def _on_save_override(self):
        """
        Internal callback function that is called when Save button is pressed
        """

        return self._override.save()

    def _on_remove_override(self):
        """
        Internal callback function that is called when Remove button is pressed
        """

        valid_remove = self._override.remove_from_node()
        if valid_remove:
            self.removed.emit()

        return self._override
