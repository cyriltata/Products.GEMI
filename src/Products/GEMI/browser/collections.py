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
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import implements

class FilterSettings(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""
    
    implements(ICollectiveGemiSettings, ICollectiveGemiCollection)

    template = ViewPageTemplateFile("templates/collections_filter_settings.pt")
    registry_key = "Products.GEMI.settings.collection_filter"
    isValid = False

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            self.saveSettings();

        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        self.populateSettings();
        return self.template();

    def saveSettings(self):
        if (self.request.form['form.submit.button'] != 'Save'):
            return;

        items = dict(self.request.form.items());

        registry = getUtility(IRegistry);
        if (registry[self.registry_key] is None):
            registry[self.registry_key] = {};

        registry[self.registry_key][self.context.id] = {
            "show": int(items.get('form.show', 0)) == 1,
            "hide": int(items.get('form.show', 0)) == 0
        };
        print items;

    def populateSettings(self):
        registry = getUtility(IRegistry);
        try:
            if (registry[self.registry_key] is not None):
                print registry[self.registry_key][self.context.id];
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
