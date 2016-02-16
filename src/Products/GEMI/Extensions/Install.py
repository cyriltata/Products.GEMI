# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
#from cStringIO import StringIO


def runProfile(portal, profileName):
    setupTool = getToolByName(portal, 'portal_setup')
    setupTool.runAllImportStepsFromProfile(profileName)

def uninstall(portal, reinstall=False):
    """Run the GS profile to uninstall this package"""
   # @todo update all objects with views 'filter_view (collections), 'navigation-like', 'listbycontenttype' (folders)
   # @todo remove added properties to objects (IProductsGEMISettings)
    if not reinstall:
        runProfile(portal, 'profile-Products.GEMI:uninstall')
