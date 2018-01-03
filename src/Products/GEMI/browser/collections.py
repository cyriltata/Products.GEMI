# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GEMI import _
from Products.GEMI import config
from Products.GEMI.config import *
from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility
from plone.app.querystring import queryparser
from plone.app.collection.interfaces import ICollection
import datetime
import random
import math


class ViewSettings(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""

    template = ViewPageTemplateFile("templates/collection_view_settings.pt")
    isValid = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.gutil = getUtility(IProductsGEMIUtility)
        self.messages = IStatusMessage(self.request)
        self.subjectKeywords = [];

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
        #util = getUtility(IProductsGEMIUtility)
        #filter_settings = util.getBibFolderFilterValues(items);
        #util.saveBibFolderFilterSettings(self.context, filter_settings);
        if ('form.save.button' in item_keys):
            return self.save(items);
        elif ('form.add.button' in item_keys):
            return self.add(items);
        elif ('form.delete.button' in item_keys):
            return self.delete(items);
        elif ('form.cancel.button' in item_keys):
            return self.cancel(items);

        self.messages.add(_(u'Your settings have been saved!'), type=u"info")
        self._redirect('/@@filter_settings?ok=1')

    def initSettings(self):
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
        self.subjectKeywords = self.context.portal_catalog.uniqueValuesFor('Subject')

    def save(self, items):
        item_keys = items.keys();
        util = self.gutil;
        n = util.getBibFolderCategoryCount(self.context) + 1;
        index = 1;

        # Save category settings
        for i in range(n+1):
            cat_name = BFV_CATEGORY % i;
            cat_types = BFV_CATEGORY_REFTYPES % i;
            cat_desc = BFV_CATEGORY_DESCRIPTION % i;
            cat_tags = BFV_CATEGORY_TAGS % i;
            category = {};
            category[cat_name] = None;

            if (cat_name in item_keys and items[cat_name]):
                category[cat_name] = {'value': items[cat_name], 'type': 'string'};
            if (cat_desc in item_keys):
                category[cat_desc] = {'value': items[cat_desc], 'type': 'text'};
            if (cat_types in item_keys):
                category[cat_types] = {'value': items[cat_types], 'type': 'lines'};
            else:
                category[cat_types] = {'value': [], 'type': 'lines'};
                
            if (cat_tags in item_keys):
                category[cat_tags] = {'value': items[cat_tags], 'type': 'lines'};
            else:
                category[cat_tags] = {'value': [], 'type': 'lines'};

            if not category[cat_name]:
                continue;

            util.saveBibFolderCategorySettings(self.context, category, index);
            index += 1;


        # Save filter settings
        filter_settings = util.getBibFolderFilterValues(items);
        util.saveBibFolderFilterSettings(self.context, filter_settings);

        self.messages.add(_(u'Your settings have been saved!'), type=u"info")
        return self._redirect('/@@filter_settings');

    def add(self, items):
        self.save(items);
        return self._redirect('/@@filter_settings?add=True');

    def delete(self, items):
        if 'category_checks' in items:
            self.gutil.deleteBibFolderCategory(self.context, items['category_checks']);
            self.gutil.reIndexBibFolderCategories(self.context);

        self.messages.add(_(u'Categories have been deleted!'), type=u"info")
        return self._redirect('/@@filter_settings');

    def cancel(self, items):
        self._redirect();

    def _redirect(self, view=None):
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
    innerView = None
    hasInnerView = False
    queries = [];

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.queries = [];

    def __call__(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        self.defineCategoryQueries();

        return self.template();

    def defineCategoryQueries(self):
        cats = [];
        bibtool = getToolByName(self, 'portal_bibliography')

        #initialize filter
        if not self.filterSettings:
            self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);

        # initialize categories
        if (self.context.hasProperty(BFV_CATEGORY_COUNT) and self.context.getProperty(BFV_CATEGORY_COUNT) > 0):
            cats = self.gutil.getBibFolderCategories(self.context, False)
        else:
            cats = [{'id': 'all', 'category': 'all', 'description': 'all', 'reftypes': None, 'tags': None}]

        for cat in cats:
            catQuery = self.getCategoryQuery(cat)
            if catQuery:
                self.queries.append(catQuery)

    def getResults(self, query=None):
        if query is None:
            query = self.getQuery();
        b_start = self.request.get('b_start', 0);
        b_size = 200
        custom_path = self.getAndCleanUpQueryLocationFilterPath()
        if (custom_path):
            query['path'] = custom_path;

        return self.context.queryCatalog(batch=True, b_start=b_start, b_size=b_size, **query)

    security.declareProtected(View, 'getCategoryQuery')
    def getCategoryQuery(self, category):
        query = self.getQuery();
        if category['category'] and category['reftypes']:
            query['portal_type'] = list(category['reftypes']);
        if category['category'] and category['tags']:
            query['Subject'] = list(category['tags']);

        labels = {
            'display_label': category['category'],
            'display_desc': category['description']
        }

        return {'filter': query, 'labels': labels};

    security.declareProtected(View, 'getQuery')
    def getQuery(self):
        query = {
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all',
        };

        # if filter is not to be shown then don't apply filter query
        #if self.filterSettings['filter_show'] != 1:
        #    return {'filter': query, 'labels': labels};

        # if there is no filter in the request then use the default filter
        if self.request.get('filter.author', None) is None:
            self.request.set('filter.author', self.filterSettings.get('filter_default_author', '').replace(',', ''))

        if self.request.get('filter.year', None) is None:
            self.request.set('filter.year', self.filterSettings.get('filter_default_year', ''))

        author = self.request.get('filter.author', '').strip().replace(',', ' ')
        author = filter(None, author.split(' '));
        author = map(str.strip, author);

        if author and author[0]:
           #query['SearchableText'] = author[0];
           query['AuthorItems'] = ' '.join(author);

        year = self.request.get('filter.year', '').strip()
        if year:
            query['publication_year'] = self.gutil.publicationYearQueryValue(year);

        return query
    
    security.declareProtected(View, 'getPdfUrl')
    def getPdfUrl(self, ref):
        return ref.getObject().download_pdf();

    @property
    def showFilter(self):
        return self.context.getProperty(BFV_FILTER_SHOW);
    
    @property
    def authorList(self):
        a = self.filterSettings.get('filter_authors', None);
        if a is None:
            a = []
        authors = list(a)
        if not authors:
            bibtool = getToolByName(self, 'portal_bibliography')
            authors = bibtool.getAllBibAuthors();
        if (len(authors) > 1):
            authors = [_('')] + authors;

        return authors

    @property
    def yearsList(self):
        y = self.filterSettings.get('filter_years', None);
        if y is None:
            y = []
        years = list(y)
        if not years:
            bibtool = getToolByName(self, 'portal_bibliography')
            years = bibtool.getAllBibYears();
        if (len(years) > 1):
            years = [_('')] + years;

        return years

    def isValidYear(self, year):
        year = year.lower().strip();
        if (year.isdigit()):
            return float(year) > 1900;
        return year

    def getAndCleanUpQueryLocationFilterPath(self):
        if not ICollection.providedBy(self.context):
            return None;

        site_path = '/'.join(self.context.portal_url.getPortalObject().getPhysicalPath());
        raw_query = queryparser.parseFormquery(self.context, self.context.getRawQuery());
        path = raw_query.get('path');
        if path and path['query']:
            for i, p in enumerate(path['query']):
                idx = p.rfind(site_path);
                if (idx > 0):
                    path['query'][i] = p[idx:];

            return path;
        return None;


class RecentPublicationsView(View):

    template = ViewPageTemplateFile('templates/collection_view_recent_publications.pt');

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.duplicates = {}
        self.items = []
        self.itr_count = 0;
        self.max_itr_count = 10;
        self.now = datetime.datetime.now();

    def __call__(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        return self.template();

    def getQuery(self):
        query = super(RecentPublicationsView, self).getQuery();
        query['path'] = {"query": "/"}
        return query;

    def getResults(self, b_start = None):
        y_size = math.floor(float(self.context.b_size) * (2.0/3.0));
        t_size = self.context.b_size - y_size;
        b_start = b_start or self.request.get('b_start', 0);
        self.getResultsByYear(b_start, t_size, 'in press');
        self.getResultsByYear(b_start, y_size, self.now.year);
        return self.items;
        
    def getResultsByYear(self, b_start=None, b_size=None, year=None, items=None):
        if (year is None):
            year = 'accepted'

        query = self.getQuery();
        query['sort_on'] = self.context.sort_on;
        if self.context.sort_reversed:
            query['sort_order'] = 'descending';
        else:
            query['sort_order'] = 'ascending';

        if (year == 'accepted'):
            query['publication_year'] = self.gutil.publicationYearQueryValue(year);
            prev_year = 'in press'
        elif (year == 'in press'):
            query['publication_year'] = self.gutil.publicationYearQueryValue(year);
            prev_year = self.now.year
        else:
            query['publication_year'] = str(year)
            prev_year = year - 1

        #b_start = b_start or self.request.get('b_start', 0);
        #b_size = self.context.b_size;
        #limit = self.context.limit;

        results = self.context.queryCatalog(batch=True, b_start=b_start, b_size=b_size * 10, **query)
        results = self.randomizeBatch(results);
        items = items or [];
        for brain in results:
            if brain.UID in self.duplicates:
                continue;
            items.append(brain)
            if (len(items) >= b_size):
                self.items.extend(items);
                return;

            self.duplicates[brain.UID] = None
            try:
                is_duplicate, matches = self.gutil.isDuplicate(self, brain.getObject(), 'global');
                if (is_duplicate):
                    for match in matches:
                        self.duplicates[match.UID()] = None
            except:
                prev_year = year
        #if results:
        #    b_start += b_size
        self.items.extend(items);
        if len(self.items) < self.context.b_size and self.itr_count < self.max_itr_count:
            self.itr_count += 1;
            self.getResultsByYear(b_start, b_size, prev_year, items)

        return items;

    def getEnableDuplicatesManager(self):
        return True;

    def randomizeBatch(self, batch):
        items = [brain for brain in batch];
        items = list(items);
        if (len(items) > 1):
            random.shuffle(items)
        return items;


def isApplicableCollectionView(view, types):
    return True;
