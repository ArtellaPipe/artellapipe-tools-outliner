#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core widgets for Artella Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from collections import defaultdict

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import search


class OutlinerTree(base.BaseWidget, object):
    """
    Core class to create outliner widgets
    """

    CATEGORIES = None
    NAME = None

    def __init__(self, project, parent=None):

        self._project = project
        self._widget_tree = defaultdict(list)
        self._widgets = list()

        super(OutlinerTree, self).__init__(parent=parent)

    def mousePressEvent(self, event):
        """
        Overrides BaseWidget mousePressEvent function
        :param event: QMouseEvent
        """

        if event.button() == Qt.LeftButton:
            tp.Dcc.clear_selection()

    def ui(self):
        super(OutlinerTree, self).ui()

        self.setMouseTracking(True)

        top_layout = QGridLayout()
        top_layout.setAlignment(Qt.AlignLeft)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self.main_layout.addLayout(top_layout)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setIcon(tp.ResourcesMgr().icon('refresh'))
        self._refresh_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._expand_all_btn = QPushButton()
        self._expand_all_btn.setIcon(tp.ResourcesMgr().icon('expand'))
        self._expand_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._collapse_all_btn = QPushButton()
        self._collapse_all_btn.setIcon(tp.ResourcesMgr().icon('collapse'))
        self._collapse_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        top_layout.addWidget(self._refresh_btn, 0, 0, 1, 1)
        top_layout.addWidget(self._expand_all_btn, 0, 1, 1, 1)
        top_layout.addWidget(self._collapse_all_btn, 0, 2, 1, 1)

        self._search_widget = search.SearchFindWidget()
        self.main_layout.addWidget(self._search_widget)

        scroll_widget = QWidget()
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setWidget(scroll_widget)

        self._outliner_layout = QVBoxLayout()
        self._outliner_layout.setContentsMargins(1, 1, 1, 1)
        self._outliner_layout.setSpacing(0)
        self._outliner_layout.addStretch()
        scroll_widget.setLayout(self._outliner_layout)
        self.main_layout.addWidget(self._scroll_area)

    def setup_signals(self):
        self._refresh_btn.clicked.connect(self._on_refresh_outliner)
        self._expand_all_btn.clicked.connect(self._on_expand_all_assets)
        self._collapse_all_btn.clicked.connect(self._on_collapse_all_assets)
        self._search_widget.textChanged.connect(self._on_search_text_changed)

    def select_item(self, asset_id):
        """
        Selects item with given id
        :param asset_id: str,
        """

        if not self._widgets:
            return

        self.clear_selection()

        for asset_widget in self._widget_tree.keys():
            if asset_widget.asset_node.id == asset_id:
                asset_widget.blockSignals(True)
                try:
                    asset_widget.set_select(True)
                    self._scroll_area.ensureWidgetVisible(asset_widget)
                finally:
                    asset_widget.blockSignals(False)

    def clear_selection(self):
        if not self._widgets:
            return

        for asset_widget in self._widget_tree.keys():
            if asset_widget._is_selected:
                asset_widget.blockSignals(True)
                try:
                    asset_widget.deselect()
                finally:
                    asset_widget.blockSignals(False)

    def append_widget(self, asset):
        """
        Adds a new outliner widget into it
        :param asset: OutlinerItem
        """

        self._widgets.append(asset)
        self._outliner_layout.insertWidget(0, asset)

    def remove_widget(self, asset):
        """
        Removes an outliner widget from it
        :param asset: OutlinerItem
        """

        if asset in self._widgets:
            for i in range(self._outliner_layout.count()):
                child = self._outliner_layout.itemAt(i)
                if child.widget() == asset:
                    child.widget().deleteLater()
                    self._widgets.pop(self._widgets.index(asset))
                    self._widget_tree.pop(asset)
                    self._outliner_layout.removeItem(child)
                    break

    def clear_items(self):
        """
        Clears all the items in the outliner
        :return:
        """
        del self._widgets[:]
        while self._outliner_layout.count():
            child = self._outliner_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self._outliner_layout.setSpacing(0)
        self._outliner_layout.addStretch()

    def refresh(self):
        """
        Refresh the items in the outliner
        """

        self._widget_tree = defaultdict(list)
        self.clear_items()
        self._init()
        can_expand = False
        for w in self._widgets:
            if w.expand_enable:
                can_expand = True
        if not can_expand:
            self._expand_all_btn.setVisible(False)
            self._collapse_all_btn.setVisible(False)

        self._on_search_text_changed(self._search_widget.get_text())

    def _init(self):
        """
        Internal callback function that initializes the outliner
        Overrides in custom outliners
        """

        pass

    def _on_refresh_outliner(self):
        """
        Internal callback function that is called when Refresh button is clicked
        :return:
        """

        self.refresh()

    def _on_expand_all_assets(self):
        """
        Internal callback function that is called when Expand button is clicked
        """

        for asset_widget in self._widget_tree.keys():
            asset_widget.expand()

    def _on_collapse_all_assets(self):
        """
        Internal callback function that is called when Collapse button is clicked
        """

        for asset_widget in self._widget_tree.keys():
            asset_widget.collapse()

    def _on_search_text_changed(self, new_text):
        all_assets = self._widget_tree.keys()
        if not new_text:
            for asset in all_assets:
                asset.setVisible(True)
        else:
            for asset in all_assets:
                if new_text in asset.name or new_text.title() in asset.name:
                    asset.setVisible(True)
                else:
                    asset.setVisible(False)
