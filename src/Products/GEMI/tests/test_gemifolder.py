# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from zope.component import queryUtility
from zope.component import createObject
from plone.app.testing import setRoles
from plone.dexterity.interfaces import IDexterityFTI
from plone import api

from Products.GEMI.testing import PRODUCTS_GEMI_INTEGRATION_TESTING  # noqa
from Products.GEMI.interfaces import IGemifolder

import unittest2 as unittest


class GemifolderIntegrationTest(unittest.TestCase):

    layer = PRODUCTS_GEMI_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name='Gemifolder')
        schema = fti.lookupSchema()
        self.assertEqual(IGemifolder, schema)

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name='Gemifolder')
        self.assertTrue(fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name='Gemifolder')
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(IGemifolder.providedBy(obj))

    def test_adding(self):
        self.portal.invokeFactory('Gemifolder', 'Gemifolder')
        self.assertTrue(
            IGemifolder.providedBy(self.portal['Gemifolder'])
        )
