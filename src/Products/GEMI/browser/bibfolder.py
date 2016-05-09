# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.GEMI.config import *
from Products.GEMI import _
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName

class View(BrowserView):

    template = ViewPageTemplateFile("templates/bibfolder_view.pt");
    queries = [];
    filterSettings = {};

    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.context = context
        self.request = request
        self.gutil = getUtility(IProductsGEMIUtility)
        self.queries = [];

    def __call__(self):
        self.initialize();
        return self.template();

    def initialize(self):
        cats = [];
        bibtool = getToolByName(self, 'portal_bibliography')

        #initialize filter
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);

        # initialize categories
        if (self.context.hasProperty(BFV_CATEGORY_COUNT) and self.context.getProperty(BFV_CATEGORY_COUNT) > 0):
            cats = self.gutil.getBibFolderCategories(self.context, False)
        else:
            cats = [{id: 'all', 'category': 'all', 'description': 'all', 'reftypes': bibtool.getReferenceTypes()}]

        for cat in cats:
            self.queries.append(self.makeCategoryQuery(cat))


    def makeCategoryQuery(self, category):
        if not category['category'] or not category['reftypes']:
            return None;

        path = '/'.join(self.context.getPhysicalPath());
        query = {
            'portal_type': list(category['reftypes']),
            'path': path,
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all',
            'display_label': category['category'],
            'display_desc': category['description']
        }

        # if filter is not to be shown then don't apply filter query
        if self.filterSettings['filter_show'] != 1:
            return query;

        # if there is no filter in the request then use the default filter
        if self.request.get('filter.author', None) is None:
            self.request.set('filter.author', self.context.getProperty(BFV_FILTER_DEFAULT_AUTHOR, ''))
            self.request.set('filter.year', self.context.getProperty(BFV_FILTER_DEFAULT_YEAR, ''))
            
        author = self.request.get('filter.author', '').strip()
        author = author.split(',');
        if author:
            query['SearchableText'] = author[0] if author else '';
        year = self.request.get('filter.year', '').strip()
        if year:
            query['publication_year'] = year;

        return query

    def runQuery(self, query, start=0, limit=1000):
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
        contentFilter = query

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

        from Products.CMFPlone import Batch
        results =  Batch(contents, b_size, b_start, orphan=0)
        if self.filterSettings['filter_by_year']:
            results = self.gutil.groupBibItemsByYears(results)
        return results
    
    @property
    def authorList(self):
        a = self.context.getProperty(BFV_FILTER_AUTHORS);
        if a is None:
            a = []
        authors = list(a)
        if not authors:
            bibtool = getToolByName(self, 'portal_bibliography')
            path = self.context.getProperty(BFV_FILTER_PATH, '/'.join(self.context.getPhysicalPath()));
            authors = bibtool.getAllBibAuthors(p=path);
        return authors
    
    @property
    def yearsList(self):
        y = self.context.getProperty(BFV_FILTER_YEARS);
        if y is None:
            y = []
        years = list(y)
        if not years:
            bibtool = getToolByName(self, 'portal_bibliography')
            path = self.context.getProperty(BFV_FILTER_PATH, '/'.join(self.context.getPhysicalPath()));
            years = bibtool.getAllBibYears(p=path);
        return years


class ViewSettings(BrowserView):

    template = ViewPageTemplateFile("templates/bibfolder_view_settings.pt")
    statusMessage = None;
    gutil = None;
    filterSettings = {};

    def __init__(self, context, request):
        super(ViewSettings, self).__init__(context, request)
        self.context = context
        self.request = request
        self.gutil = getUtility(IProductsGEMIUtility)
        self.messages = IStatusMessage(self.request)

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            """ Save the settings when a POST request is sent """
            return self.postRequest();

        self.initSettings();
        return self.template();
    
    def initSettings(self):
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
    
    def postRequest(self):
        items = dict(self.request.form.items());
        item_keys = items.keys();

        if ('form.submitted' not in item_keys):
            self._redirect();
            return;
        
        if ('form.save.button' in item_keys):
            return self.save(items);
        elif ('form.add.button' in item_keys):
            return self.add(items);
        elif ('form.delete.button' in item_keys):
            return self.delete(items);
        elif ('form.cancel.button' in item_keys):
            return self.cancel(items);

        return self.template();

    def save(self, items):
        item_keys = items.keys();
        util = self.gutil;
        n = util.getBibFolderCategoryCount(self.context) + 1;

        # Save categories
        for i in range(n+1):
            cat_name = BFV_CATEGORY % i;
            cat_types = BFV_CATEGORY_REFTYPES % i;
            cat_desc = BFV_CATEGORY_DESCRIPTION % i;
            if (cat_name in item_keys and cat_types in item_keys):
                if (self.context.hasProperty(cat_name)):
                    util.modifyBibFolderCategory(self.context, i, items[cat_name], items[cat_types], items[cat_desc])
                else:
                    util.addBibFolderCategory(self.context, items[cat_name], items[cat_types], items[cat_desc])

        # Save filter settings
        filter_settings = util.getBibFolderFilterValues(items);
        util.saveBibFolderFilterSettings(self.context, filter_settings);

        self.messages.add(_(u'Your settings have been saved!'), type=u"info")
        return self._redirect('bibfolder-view-settings-gemi');

    def add(self, items):
        self.save(items);
        return self._redirect('bibfolder-view-settings-gemi?add=True');

    def delete(self, items):
        if 'category_checks' in items:
            self.gutil.deleteBibFolderCategory(self.context, items['category_checks']);
            self.gutil.reIndexBibFolderCategories(self.context);

        self.messages.add(_(u'Categories have been deleted!'), type=u"info")
        return self._redirect('bibfolder-view-settings-gemi');

    def cancel(self, items):
        self._redirect();

    def _redirect(self, view = None):
        if (view is None):
            view = ''
        contextURL = "%s/%s" % (self.context.absolute_url(), view)
        self.request.response.redirect(contextURL)
        
class ViewListFormatter(BrowserView):

    template = ViewPageTemplateFile('templates/bibfolder_view_item.pt')

    def __call__(self, item=None):
        self.item = item.getObject()
        return self.template()
    
    def formatVolume(self):
        v = '';
        if (hasattr(self.item, 'volume')):
            v += self.item.getVolume()
        if (hasattr(self.item, 'number')):
            num = self.item.getNumber();
            if num:
                v += '('+num+')';
        if v:
            v = ', ' + v + ', ';
        return v;
    
    def getJournal(self):
        if (not hasattr(self.item, 'journal')):
            return False
        return self.item.getJournal();

    def getPdfUrl(self):
        r = self.item;
        if (r.getPdf_url()):
            url = r.getPdf_url()
        elif (r.getPdf_file()):
            pdf = r.getPdf_file();
            url = pdf.absolute_url();
        else:
            url = None

        return url;

    def getUrl(self):
        if self.item.getPublication_url():
            return self.item.getPublication_url()
        return None
