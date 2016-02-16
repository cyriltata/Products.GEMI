# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.registry.interfaces import IRegistry

from zope.component import getUtility
from zope.component import getMultiAdapter

from Products.GEMI.interfaces import IStatusMessage
from Products.GEMI.interfaces import IProductsGEMISettings
from Products.GEMI.interfaces import IObject
from Products.GEMI.portaltypes import types as portaltypes
from Products.GEMI import _

HAS_SECURITY_SETTINGS = True
try:
    from Products.CMFPlone.interfaces import ISecuritySchema
except ImportError:
    HAS_SECURITY_SETTINGS = False


class NavigationLikeView(BrowserView):

    """
    List summary information for items in the folder except those exluded from navigation

    Batch results.
    """

    template = ViewPageTemplateFile("templates/folders_navigation_like.pt")

    def __init__(self, context, request):
        super(NavigationLikeView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((context, request), name=u"plone")
        self.portal_state = getMultiAdapter((context, request), name=u"plone_portal_state")
        self.pas_member = getMultiAdapter( (context, request), name=u"pas_member")

    def __call__(self):
        """ Render the content item listing. """

        # How many items is one one page
        limit = 50

        # What kind of query we perform?
        # Here we limit results to ProductCard content type
        filter = {"show_excluded_from_nav": False}

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
        contents = self.context.portal_catalog(contentFilter, show_all=1, show_inactive=show_inactive,)

        # remove contents exluded from navigation if asked for
        filtered = []
        if not contentFilter['show_excluded_from_nav']:
            for brain in contents:
                if (not getattr(brain, 'exclude_from_nav', False)):
                    filtered.append(brain);
        else:
            filtered = contents

        from Products.CMFPlone import Batch
        return Batch(filtered, b_size, b_start, orphan=0)

    def normalizeString(self, text):
        return self.plone_view.normalizeString(text);

    def toLocalizedTime(self, time, long_format=None, time_only=None):
        return self.plone_view.toLocalizedTime(time, long_format, time_only)


class ContentTypeView(NavigationLikeView):
    """
    Show a folder listing according to enabled content types
    """

    def __init__(self, context, request):
        super(ContentTypeView, self).__init__(context, request)

    def __call__(self):
        """ Render the content item listing. """

        # How many items is one one page
        limit = 50

        # What kind of query we perform?
        # Here we limit results to ProductCard content type
        
        # To get settings, first we check if settings are present in current context
        # if not we get settings from the control panel
        object = self.context
        if (object.hasProperty('show_nav_exluded_items')):
            settings = IObject
            settings.show_nav_exluded_items = object.getProperty('show_nav_exluded_items')
            settings.allowed_content_types = object.getProperty('allowed_content_types')
            
        else:
            registry = getUtility(IRegistry);
            settings = registry.forInterface(IProductsGEMISettings)

        filter = {
            "show_excluded_from_nav": settings.show_nav_exluded_items,
            "portal_type": settings.allowed_content_types
        }
        

        # Read the first index of the selected batch parameter as HTTP GET request query parameter
        start = self.request.get("b_start", 0)

        # Perform portal_catalog query
        self.contents = self.query(start, limit, filter)

        # Return the rendered template (productcardsummaryview.pt), with content listing information filled in
        return self.template();

import math

class ContentTypeSettingsView(BrowserView):
    """
    Class to handle content-type view settings for
    a particular folder. If these settings are not set for some folder,
    then settings from the general control panel come into effect
    """
    
    template = ViewPageTemplateFile("templates/folders_contenttype_view_settings.pt")

    def __init__(self, context, request):
        super(ContentTypeSettingsView, self).__init__(context, request)
        self.context = context
        self.request = request

    schema = IProductsGEMISettings

    label = _(u"Settings for Content-type folder view")
    description = _(u"help_contenttype_view_settings",
                    default=u"Configure what content types should be shown when the 'Content-type view' is selected for this folder")

    settingsFields = [
        {
            'id': 'show_nav_exluded_items',
            'type': 'boolean',
            'value': True
        },
        {
            'id': 'allowed_content_types',
            'type': 'list',
            'value': 'value'
        }
    ]

    settingsValues = {}
    
    statusMessage = None

    def __init(self):
        self.statusMessage = None

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            """ Save the settings when a POST request is sent """
            return self.saveSettings();

        self.initSettings();
        return self.template();

    def initSettings(self):
        object = self.context
        for f in self.settingsFields:
            if (not object.hasProperty(f['id'])):
                continue
            self.settingsValues[f['id']] = object.getProperty(f['id']);

        try:
            if self.request.form['ok']:
                self.statusMessage = IStatusMessage(_(u'Your settings have been saved!'), _(u'Saved'), 'info')
        except KeyError:
            pass

    def saveSettings(self):
        object = self.context
        settings = {}
        data = {}
        items = dict(self.request.form.items());
        item_keys = items.keys();

        if ('form.submitted' not in item_keys or 'form.cancel.button' in item_keys):
            self._redirect();
            return;

        # Gather all submitted items in the 'data' dict
        data['show_nav_exluded_items'] = 'form.show_nav_exluded_items' in item_keys

        if ('form.allowed_content_types' in item_keys):
            if type(items['form.allowed_content_types']) is not list:
                items['form.allowed_content_types'] = [items['form.allowed_content_types']];
            data['allowed_content_types'] = items['form.allowed_content_types']
        else:
            data['allowed_content_types'] = []

        # Get all property items of object and save them too or they get overwritten
        for p in object.propertyMap():
            settings[p['id']] = object.getProperty(p['id'])
            
        # Save various items
        for f in self.settingsFields:
            if (object.hasProperty(f['id'])):
                settings[f['id']] = data[f['id']]
            else:
                object.manage_addProperty(type=f['type'], id=f['id'], value=data[f['id']])

        object.manage_changeProperties(settings)

        self._redirect('/listbycontenttype-settings?ok=1');
        return self.template();

    def getSetting(self, key):
        try:
            return self.settingsValues[key];
        except KeyError:
            return None

    def typeSelected(self, type):
        try:
            return type in self.settingsValues['allowed_content_types'];
        except KeyError:
            return False

    @property
    def groupedTypes(self):
        types = portaltypes()
        per_col = math.ceil(len(types) / 3) + 1
        groups = []
        group = []
        for i in range(0, len(types)):
            group.append(types[i])
            if i > 0 and i % per_col == 0:
                groups.append(group)
                group = []

        if len(group) > 0:
            groups.append(group)

        return groups

    def _redirect(self, view = None):
        if (view is None):
            view = ''
        contextURL = "%s%s" % (self.context.absolute_url(), view)
        self.request.response.redirect(contextURL)


