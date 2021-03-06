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
from HTMLParser import HTMLParser

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
            cats = [{'id': 'all', 'category': 'all', 'description': 'all', 'reftypes': bibtool.getReferenceTypes(), 'tags': None}]

        for cat in cats:
            self.queries.append(self.getCategoryQuery(cat))


    def getCategoryQuery(self, category):
        path = '/'.join(self.context.getPhysicalPath());
        query = {
            'path': {'query': path, 'depth': 1},
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all'
        }
        if category['category'] and category['reftypes']:
            query['portal_type'] = list(category['reftypes']);
        if category['category'] and category['tags']:
            query['Subject'] = list(category['tags']);

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
            query['publication_year'] = self.gutil.publicationYearQueryValue(year);

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
            return self.gutil.groupBibItemsByYears(results)

        return self.gutil.sortByFirstAuthor(results, True)
    
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
            path = self.context.getProperty(BFV_FILTER_PATH, '/'.join(self.context.getPhysicalPath()));
            years = bibtool.getAllBibYears(p=path);
        if (len(years) > 1):
            years = [_('')] + years;
        return years

    def isValidYear(self, year):
        year = year.lower().strip();
        if (year.isdigit()):
            return float(year) > 1900;
        return year


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
        self.subjectKeywords = []

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "POST"):
            """ Save the settings when a POST request is sent """
            return self.postRequest();

        self.initSettings();
        return self.template();
    
    def initSettings(self):
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
        self.subjectKeywords = self.context.portal_catalog.uniqueValuesFor('Subject');
    
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

        # Save category settings
        index = 1;
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

    def __init__(self, context, request):
        super(ViewListFormatter, self).__init__(context, request);
        self.htmlparser = HTMLParser();

    def __call__(self, item=None):
        if (item is None):
            return None;
        self.item = item.getObject()
        return self.template()

    def Title(self):
        t = self.item.Title().strip('.');
        return t + '.'

    def formatVolume(self):
        v = '';
        if (getattr(self.item, 'volume', None)):
            v += "<i>%s</i>" % self.item.getVolume()
        if (getattr(self.item, 'number', None)):
            v += '('+self.item.getNumber()+')';
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
        return self.item.download_pdf()

    def getUrl(self):
        if self.item.getPublication_url():
            return self.item.getPublication_url()
        return None

    def getFormattedIdentifiers(self):
        if (not hasattr(self.item, 'identifiers')):
            return None
        try:
            s = ' '.join([self.getFormattedIdentifier(identifier) for identifier in self.item.getIdentifiers()]).strip(',').strip();
            if s:
                return s + '.';
        except:
            return None;

    def getFormattedIdentifier(self, identifier):
        if (identifier['label'] == 'DOI'):
            idf = identifier['value'] if ("doi.org" in identifier['value']) else "https://dx.doi.org/" + identifier['value']
            return " %s," % idf
        else:
            return " %s: %s," % (identifier['label'], identifier['value'])
        

    def getPages(self):
        if (getattr(self.item, 'pages', None)):
            return self.htmlparser.unescape(self.item.getPages()) + '.'
        return None;

    def inBook(self):
        """ chapter, pages. Publisher: Address """
        book = [];
        if (hasattr(self.item, 'chapter')):
            book.append(self.item.getChapter())
        if (getattr(self.item, 'pages', None)):
            book.append('pp. ' + self.item.getPages())
        book = filter(None, book);

        s = '';

        if book:
            s += '(' + ', '.join(book) + ').'
        if (getattr(self.item, 'publisher', None) and not self.item.getAddress()):
            s += ' %s.' % self.item.getPublisher()
        elif (getattr(self.item, 'publisher', None) and self.item.getAddress()):
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
        if getattr(self.item, 'editor', None):
            return 'In ' + self.item.getEditor() + ', '
        return None;

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
        if (getattr(self.item, 'edition', None)):
            return ' (' + self.item.getEdition() + ').'
        return None;


