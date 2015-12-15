# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from Products.GEMI.testing import PRODUCTS_GEMI_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that Products.GEMI is properly installed."""

    layer = PRODUCTS_GEMI_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if Products.GEMI is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'Products.GEMI'))

    def test_browserlayer(self):
        """Test that IProductsGemiLayer is registered."""
        from Products.GEMI.interfaces import (
            IProductsGemiLayer)
        from plone.browserlayer import utils
        self.assertIn(IProductsGemiLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PRODUCTS_GEMI_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['Products.GEMI'])

    def test_product_uninstalled(self):
        """Test if Products.GEMI is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'Products.GEMI'))
