# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.GEMI.config import *
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface import IATTopic

from zope.component import getUtility

from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.GEMI import config
from Products.GEMI import _

class ViewSettings(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""

    template = ViewPageTemplateFile("templates/collection_view_settings.pt")
    isValid = False

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
        items = dict(self.request.form.items());
        item_keys = items.keys();

        if ('form.submitted' not in item_keys or 'form.cancel.button' in item_keys):
            self._redirect();
            return;
        
        # Save filter settings
        authors = filter(None, items.get('filter_authors', '').splitlines());
        authors.sort();
        years = filter(None, items.get('filter_years', '').splitlines());
        years.sort();
        filter_settings = {
            BFV_FILTER_SHOW : {'type':'int', 'value': int(items.get('filter_show', False) == 'True')},
            BFV_FILTER_BY_YEAR : {'type':'int', 'value': int(items.get('filter_by_year', False) == 'True')},
            BFV_FILTER_AUTHORS : {'type':'lines', 'value': authors},
            BFV_FILTER_YEARS : {'type':'lines', 'value': years},
        };
        util = getUtility(IProductsGEMIUtility)
        util.saveBibFolderFilterSettings(self.context, filter_settings);

        messages = IStatusMessage(self.request)
        messages.add(_(u'Your settings have been saved!'), type=u"info")
        self._redirect('/@@filter_settings?ok=1')

    def initSettings(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);

    def _redirect(self, view = None):
        if (view is None):
            view = ''
        contextURL = "%s%s" % (self.context.absolute_url(), view)
        self.request.response.redirect(contextURL)


class View(BrowserView):

    security = ClassSecurityInfo();
    template = ViewPageTemplateFile("templates/collection_view.pt");
    isValid = False
    gutil = None;
    filterSettings = {};

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        return self.template();

    def getResults(self):
        query = self.getQuery();
        b_start = self.request.get('b_start', 0);

        if IATTopic.providedBy(self.context):
            return self.context.queryCatalog(query, batch=True, b_start=b_start);
        else:
           return self.context.results(b_start=b_start, custom_query=query)

    security.declareProtected(View, 'getQuery')
    def getQuery(self):
        query = {
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all',
        };

        author = self.request.get('filter.author', '').strip()
        author = author.split(',');
        if author:
            query['SearchableText'] = author[0] if author else '';
        year = self.request.get('filter.year', '').strip()
        if year:
            query['publication_year'] = year;

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
        return self.context.getProperty(BFV_FILTER_SHOW);
    
    @property
    def authorList(self):
        a = self.context.getProperty(BFV_FILTER_AUTHORS);
        if a is None:
            a = []
        authors = list(a)
        if not authors:
            bibtool = getToolByName(self, 'portal_bibliography')
            authors = bibtool.getAllBibAuthors();
        return authors

    @property
    def yearsList(self):
        y = self.context.getProperty(BFV_FILTER_YEARS);
        if y is None:
            y = []
        years = list(y)
        if not years:
            bibtool = getToolByName(self, 'portal_bibliography')
            years = bibtool.getAllBibYears();
        return years


def isApplicableCollectionView(view, types):
    if IATTopic.providedBy(view.context):
        items = view.context.queryCatalog({'portal_type': types}, batch=True, b_size=3)
    else:
        items = view.context.results(b_start=0, b_size=3, custom_query={'portal_type': types});

    if (items is not None):
        for brain in items:
            if (not brain.portal_type in types):
                return False
        return True

    return False;
