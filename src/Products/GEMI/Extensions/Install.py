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

def update_views(brains, original, target):
    for brain in brains:
        obj = brain.getObject()
        if getattr(obj, "layout", None) in original:
            print "Updated:" + obj.absolute_url()
            obj.setLayout(target)
    
def update_folder_views(portal):
    portal_catalog = getToolByName(portal, 'portal_catalog')
    brains = portal_catalog(portal_type="Folder")
    original = ('navigation-like', 'listbycontenttype')
    target = 'folder_listing'
    update_views(brains, original, target)

def update_collection_views(portal):
    portal_catalog = getToolByName(portal, 'portal_catalog')
    brains = portal_catalog(portal_type=("Collection", "Topic"))
    original = ('filter_view')
    target = 'standard_view'
    update_views(brains, original, target)

