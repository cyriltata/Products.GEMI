from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

def types():
    """ List user-selectable content types.

    We cannot use the method provided by the IPortalState utility view,
    because the vocabulary factory must be available in contexts where
    there is no HTTP request (e.g. when installing add-on product).

    This code is copied (but modified) from
    https://github.com/plone/plone.app.layout/blob/master/plone/app/layout/globals/portal.py

    @return: Generator for (id, type_info title) tuples
    """

    site = getSite()
    context = aq_inner(site)
    site_properties = getToolByName(context, "portal_properties").site_properties
    not_searched = site_properties.getProperty('types_not_searched', [])

    portal_types = getToolByName(context, "portal_types")
    types = portal_types.listContentTypes()

    # Get list of content type ids which are not filtered out
    prepared_types = [t for t in types if t not in not_searched]

    # Return (id, title) pairs
    types = [{'id': id, 'title': portal_types[id].title} for id in prepared_types ]

    return types

