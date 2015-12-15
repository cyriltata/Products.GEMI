# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import Products.GEMI


class ProductsGemiLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=Products.GEMI)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'Products.GEMI:default')


PRODUCTS_GEMI_FIXTURE = ProductsGemiLayer()


PRODUCTS_GEMI_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PRODUCTS_GEMI_FIXTURE,),
    name='ProductsGemiLayer:IntegrationTesting'
)


PRODUCTS_GEMI_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PRODUCTS_GEMI_FIXTURE,),
    name='ProductsGemiLayer:FunctionalTesting'
)


PRODUCTS_GEMI_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PRODUCTS_GEMI_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='ProductsGemiLayer:AcceptanceTesting'
)
