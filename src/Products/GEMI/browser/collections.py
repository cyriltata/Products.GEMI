# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GEMI.interfaces import ICollectiveGemiCollection
from Products.GEMI.interfaces import ICollectiveGemiSettings
from Products.GEMI import config
from Products.GEMI import _
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import implements

class FilterSettings(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""
    
    implements(ICollectiveGemiSettings, ICollectiveGemiCollection)

    template = ViewPageTemplateFile("templates/collections_filter_settings.pt")
    registry_key = "Products.GEMI.settings.collection_filter"
    isValid = False

    _settings = (
        {'id':'pg_show_collection_filter',
         'type':'boolean',
         'mode':'w'
        },
    );

    _default_settings = {
        'pg_show_collection_filter': True,
    }

    _current_settings = {}

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            self.saveSettings();
            self.context.plone_utils.addPortalMessage(_(u'Settings saved'), 'info')
            self.request.response.redirect(self.context.absolute_url()+'/@@filter_settings?ok=1')

        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        self.initSettings();
        self.populateSettings();
        return self.template();

    def saveSettings(self):
        if (self.request.form['form.submit.button'] != 'Save'):
            return;

        items = dict(self.request.form.items());

        settings = {
            "pg_show_collection_filter": int(items.get('pg_show_collection_filter', 0)) == 1,
        }
        prop_src = self.context;
        for p in prop_src.propertyMap():
            if p['id'] != 'title' and not p['id'] in settings:
                settings[p['id']] = prop_src.getProperty(p['id'])
        self.context.manage_changeProperties(settings);

    def populateSettings(self):
        for p in self._settings:
            self._current_settings[p['id']] = self.context.getProperty(p['id']);

    def initSettings(self, force = False):
        coll = self.context;
        if (coll.hasProperty('pg_show_collection_filter') and not force):
            #print "Collection already has settings initialized";
            return;

        for p in self._settings:
            coll.manage_addProperty(type=p['type'], id=p['id'], value=self._default_settings[p['id']])

    def getSetting(self, key):
        try:
            return self._current_settings[key];
        except KeyError:
            pass;
        


class FilterView(BrowserView):
    
    implements(ICollectiveGemiCollection)

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
        query = {'sort_on': 'publication_year'};

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


def isApplicableCollectionView(view, types):
    items = view.context.results(b_start=0, b_size=3);
    if (items is not None):
        for brain in items:
            if (not brain.portal_type in types):
                return False
        return True

    return False;
