# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema
from zope.interface import Interface
from zope.interface import implements
from zope.component import getMultiAdapter
from plone.registry.interfaces import IRegistry

HAS_SECURITY_SETTINGS = True
try:
    from Products.CMFPlone.interfaces import ISecuritySchema
except ImportError:
    HAS_SECURITY_SETTINGS = False


class TodoView(BrowserView):

    """
    List summary information for items in the folder except those exluded from navigation

    Batch results.
    """

    template = ViewPageTemplateFile("templates/folders_todo.pt")

    def __init__(self, context, request):
        super(TodoView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((context, request), name=u"plone")
        self.portal_state = getMultiAdapter((context, request), name=u"plone_portal_state")
        self.pas_member = getMultiAdapter( (context, request), name=u"pas_member")

    def __call__(self):
        """ Render the content item listing. """

        # How many items is one one page
        limit = 100

        # What kind of query we perform?
        # Here we limit results to ProductCard content type
        filter = {}

        # Read the first index of the selected batch parameter as HTTP GET request query parameter
        start = self.request.get("b_start", 0)

        # Perform portal_catalog query
        self.contents = self.query(start, limit, filter)

        # Return the rendered template (productcardsummaryview.pt), with content listing information filled in
        return self.template();

    @property
    def isAnon(self):
        return self.portal_state.anonymous()

    @property
    def navigation_root_url(self):
        return self.portal_state.navigation_root_url()

    @property
    def show_about(self):
        if not HAS_SECURITY_SETTINGS:
            # BBB
            site_props = self.context.restrictedTraverse(
                'portal_properties').site_properties
            show_about = getattr(site_props, 'allowAnonymousViewAbout', False)
        else:
            registry = getUtility(IRegistry)
            settings = registry.forInterface(ISecuritySchema, prefix="plone")
            show_about = getattr(settings, 'allow_anon_views_about', False)
        return show_about or not self.isAnon

    def query(self, start, limit, contentFilter):
        """ Make catalog query for the folder listing.

        @param start: First index to query

        @param limit: maximum number of items in the batch

        @param contentFilter: portal_catalog filtering dictionary with index -> value pairs.

        @return: Products.CMFPlone.PloneBatch.Batch object
        """

        # Batch size
        b_size = limit

        # Batch start index, zero based
        b_start = start

        # set to content filter
        mtool = self.context.portal_membership
        cur_path = '/'.join(self.context.getPhysicalPath())
        path = {}

        if not contentFilter:
            contentFilter = {}
        else:
            contentFilter = dict(contentFilter)

        if not contentFilter.get('sort_on', None):
            contentFilter['sort_on'] = 'getObjPositionInParent'

        if contentFilter.get('path', None) is None:
            path['query'] = cur_path
            path['depth'] = 1
            contentFilter['path'] = path

        # Folder or Large Folder like content
        show_inactive = mtool.checkPermission('Access inactive portal content', self.context)
        contents = self.context.portal_catalog(contentFilter, exclude_from_nav=0, show_all=1, show_inactive=show_inactive,)

        # remove contents exluded from navigation
        filtered = []
        for brain in contents:
            if (not getattr(brain, 'exclude_from_nav', False)):
                filtered.append(brain);

        from Products.CMFPlone import Batch
        return Batch(filtered, b_size, b_start, orphan=0)

    def normalizeString(self, text):
        return self.plone_view.normalizeString(text);

    def toLocalizedTime(self, time, long_format=None, time_only=None):
        return self.plone_view.toLocalizedTime(time, long_format, time_only)


