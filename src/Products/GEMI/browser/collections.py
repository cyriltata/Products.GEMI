# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from Products.GEMI.interfaces import IProductsGEMISettings
from Products.GEMI.interfaces import IStatusMessage
from Products.GEMI import config
from Products.GEMI import _

class FilterViewSettings(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""

    template = ViewPageTemplateFile("templates/collections_filter_settings.pt")
    isValid = False
    
    settingsFields = [
        {
            'id': 'show_collection_filter',
            'type': 'boolean',
            'value': True
        },
    ]

    settingsValues = {}

    statusMessage = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            return self.saveSettings();

        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        self.initSettings();
        return self.template();

    def saveSettings(self):
        object = self.context
        items = dict(self.request.form.items());
        item_keys = items.keys();
        data = {}
        settings = {}

        if ('form.submitted' not in item_keys or 'form.cancel.button' in item_keys):
            self._redirect();
            return;
        
        # Gather all submitted items in the 'data' dict
        data['show_collection_filter'] = 'show_collection_filter' in item_keys

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

        #self.context.plone_utils.addPortalMessage(_(u'Settings saved'), 'info')
        self._redirect('/@@filter_settings?ok=1')

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

    def getSetting(self, key):
        try:
            return self.settingsValues[key];
        except KeyError:
            pass;

    def _redirect(self, view = None):
        if (view is None):
            view = ''
        contextURL = "%s%s" % (self.context.absolute_url(), view)
        self.request.response.redirect(contextURL)
        


class FilterView(BrowserView):

    security = ClassSecurityInfo();
    template = ViewPageTemplateFile("templates/collections_filter_view.pt");
    isValid = False

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        return self.template();

    security.declareProtected(View, 'getQuery')
    def getQuery(self):
        items = dict(self.request.form.items());
        query = {
            'sort_on': 'publication_year',
            'sort_order': 'reverse'
        };

        author = items.get('author', None);
        if (author is not None and author.strip() != ''):
            lastname, fl = author.split(',');
            query['SearchableText'] = lastname;

        year = items.get('year', None);
        if (year is not None and year.strip() != ''):
            query['publication_year'] = items.get('year');

        return query
    
    security.declareProtected(View, 'getPdfUrl')
    def getPdfUrl(self, ref):
        r = ref.getObject();
        if (r.getPdf_url()):
            url = r.getPdf_url()
        elif (r.getPdf_file()):
            pdf = r.getPdf_file();
            url = pdf.absolute_url();
        else:
            url = None

        return url;

    @property
    def showFilter(self):
        # To get settings, first we check if settings are present in current context
        # if not we get settings from the control panel
        if self.context.hasProperty('show_collection_filter'):
            return self.context.getProperty('show_collection_filter')
        else:
            registry = getUtility(IRegistry);
            settings = registry.forInterface(IProductsGEMISettings)
            return settings.show_collection_filter


def isApplicableCollectionView(view, types):
    items = view.context.results(b_start=0, b_size=3);
    if (items is not None):
        for brain in items:
            if (not brain.portal_type in types):
                return False
        return True

    return False;
