#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains general tests for artellapipe-tools-outliner
"""

import pytest

from artellapipe.tools.outliner import __version__


def test_version():
    assert __version__.__version__
