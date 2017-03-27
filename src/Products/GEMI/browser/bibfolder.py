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
        if not self.filterSettings:
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
            'path': {'query': path, 'depth': 1},
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all'
        }
        labels = {
            'display_label': category['category'],
            'display_desc': category['description']
        }

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
            query['publication_year'] = year;

        return {'filter': query, 'labels': labels};

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
        contentFilter = query['filter']

        if not contentFilter:
            contentFilter = {}
        else:
            contentFilter = dict(contentFilter)

        if not contentFilter.get('sort_on', None):
            contentFilter['sort_on'] = 'getObjPositionInParent'

        path = contentFilter.get('path', None);
        if path is None:
            path = {'query': cur_path, 'depth': 1}
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
        a = self.filterSettings.get('filter_authors', None);
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
        y = self.filterSettings.get('filter_years', None);
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

    def Title(self):
        t = self.item.Title().strip('.');
        return t + '.'

    def formatVolume(self):
        v = '';
        if (hasattr(self.item, 'volume')):
            v += self.item.getVolume()
        if (hasattr(self.item, 'number')):
            num = self.item.getNumber();
            if num:
                v += '('+num+')';
        v = v.strip();
        if v and self.getPages():
            v = v + ', ';
        elif v and not self.getPages():
            v = v + '.'

        return v;
    
    def getJournal(self):
        if (not hasattr(self.item, 'journal')):
            return False
        journal = self.item.getJournal();
        if self.formatVolume():
            journal += ', ';
        else:
            journal += '.';

        return journal;

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

    def getFormattedIdentifiers(self):
        if (not hasattr(self.item, 'identifiers')):
            return None
        s = ' '.join([" %s:%s," % (identifier['label'], identifier['value']) for identifier in self.item.getIdentifiers()]).strip(',').strip();
        if s:
            return s + '.';

    @property
    def getPages(self):
        if (hasattr(self.item, 'pages') and self.item.getPages()):
            return self.item.getPages() + '.'

    def inBook(self):
        """ chapter, pages. Publisher: Address """
        book = [];
        if (hasattr(self.item, 'chapter')):
            book.append(self.item.getChapter())
        if (hasattr(self.item, 'pages')):
            book.append(self.item.getPages())
        book = filter(None, book);

        s = '';

        if book:
            s += ', '.join(book) + '.'
        if (hasattr(self.item, 'publisher') and not self.item.getAddress()):
            s += ' %s.' % self.item.getPublisher()
        elif (hasattr(self.item, 'publisher') and self.item.getAddress()):
            s += ' %s: %s.' % (self.item.getAddress(), self.item.getPublisher())

        return s;

    @property
    def Authors(self):
        if (hasattr(self.item, 'AuthorItems')):
            authors = self.item.getAuthors();
            _list = [];
            for a in authors:
                _a = a.get('lastname') + ', ';
                if a.get('firstname'):
                    _a += a.get('firstname')[0] + '.'
                if a.get('middlename'):
                    _a += a.get('middlename')[0] + '.'
                if len(_list) > 0:
                    _a = ', ' + _a

                _list.append(_a);

            if len(_list) > 1:
                lastIndex = len(_list) - 1;
                _list[lastIndex] = ' & '+ _list[lastIndex].strip(',');

            return ''.join(_list);
        return None;

    @property
    def Editors(self):
        if not hasattr(self.item, 'editor'):
            return None;

        if self.item.getEditor():
            return 'In ' + self.item.getEditor() + ', '

    @property
    def BookTitle(self):
        if not hasattr(self.item, 'booktitle'):
            return None;

        s = '';
        if not self.Editors:
            s += 'In '
        s += self.item.getBooktitle();
        return s + '.';

    @property
    def Edition(self):
        if not hasattr(self.item, 'edition'):
            return None;

        if (self.item.getEdition()):
            return ' (' + self.item.getEdition + ').'

    

class ViewContent(BrowserView):

    template = ViewPageTemplateFile('templates/bibfolder_content.pt')

    def __call__(self, p=None):
        self.parent = p
        return self.template()
