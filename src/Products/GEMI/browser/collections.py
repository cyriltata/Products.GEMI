# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.interface import IATTopic
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GEMI import _
from Products.GEMI import config
from Products.GEMI.config import *
from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFBibliographyAT.interface import IBibliographyFolder
from zope.component import getUtility
from plone.batching import Batch
from plone.app.querystring import queryparser
from Acquisition import aq_acquire
from Acquisition import aq_inner
from Acquisition import aq_base
from zope.component import getMultiAdapter

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
        util = getUtility(IProductsGEMIUtility)
        filter_settings = util.getBibFolderFilterValues(items);
        util.saveBibFolderFilterSettings(self.context, filter_settings);

        messages = IStatusMessage(self.request)
        messages.add(_(u'Your settings have been saved!'), type=u"info")
        self._redirect('/@@filter_settings?ok=1')

    def initSettings(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);

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

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        self.filterSettings = self.gutil.getBibFolderFilterSettings(self.context);
        self.isValid = isApplicableCollectionView(self, config.ALLOWED_TYPES_COLLECTION_FILTER_VIEW);
        if self.filterSettings['show_folder_in_collection'] == 1:
            return self.folder_template();
        else:
            return self.template();

    def folder_template(self):
        obj = None;
        if IATTopic.providedBy(self.context):
            query = self.context.buildQuery();
        else:
            query = queryparser.parseFormquery(self.context, self.context.getRawQuery()) 

        if (query.get('path')):
            path = query.get('path')
            name = 'bibfolder-view-gemi';
            if IATTopic.providedBy(self.context):
                target_obj = self.context.restrictedTraverse(path.get('query'))
            else:
                target_obj = self.context.restrictedTraverse(path.get('query')[0])

            obj = aq_inner(target_obj)
            if IBibliographyFolder.providedBy(obj):
                # May raise ComponentLookUpError
                view = getMultiAdapter((obj, self.request), name=name)
                # Overwrite filter settings with those in collection
                view.filterSettings = self.filterSettings;
                # Add the view to the acquisition chain
                view = view.__of__(obj)
                self.hasInnerView = True
                self.innerView = view
                return self.template()

        return 'ERROR/OBJECT/M.I';

    def getResults(self):
        query = self.getQuery();
        b_start = self.request.get('b_start', 0);
        b_size = 200
        return self.context.queryCatalog(batch=True, b_start=b_start, b_size=b_size, **query)
#        if IATTopic.providedBy(self.context):
#            query = self.getQuery()
#            query.update(self.getTopicQuery())
#            results = self.context.portal_catalog(**query);
#            return Batch(results, b_size, b_start, orphan=0)
#        else:
#            return self.context.results(b_start=b_start, custom_query=query)

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

    def getTopicQuery(self):
        catalog = self.context.portal_catalog
        topic = self.context
        query = topic.buildQuery()
        #query.pop('sort_order', None)

        for criterion in topic.listCriteria():
            if criterion.meta_type in ['ATDateRangeCriterion', 'ATFriendlyDateCriteria']:
                start_date, end_date = self.gutil.getStartEnd(topic, criterion, catalog)
                value = (start_date.strftime('%Y/%m/%d'), end_date.strftime('%Y/%m/%d'))
            else:
                value = None

            if value:
                query[criterion.Field()] = {}
                if hasattr(criterion, 'getOperator'):
                    operator = criterion.getOperator()
                    query[criterion.Field()]['operator'] = operator
                    assert(criterion.meta_type in ['ATSelectionCriterion', 'ATListCriterion'])
                else:
                    operator = None
                if operator == 'or':
                    query[criterion.Field()] = {'query':[value], 'operator':'or'}
                elif operator == 'and':
                    q = list(criterion.Value()) + [value]
                    query[criterion.Field()] = {'query':[q], 'operator':'and'}
                else:
                    if criterion.meta_type in ['ATDateRangeCriterion', 'ATFriendlyDateCriteria']:
                        start = DateTime(value[0])
                        end = DateTime(value[1])
                        query[criterion.Field()] = {'query':(start, end), 'range': 'min:max'}
                    else:
                        assert(criterion.meta_type == 'ATSimpleStringCriterion')
                        if criterion.Value():
                            query[criterion.Field()] = {'query': [criterion.Value(), value], 'operator':'and'}
                        else:
                            query[criterion.Field()] = value
            else:
                continue

        #get sort_on/order out of topic
        sort_on = 'publication_year'
        sort_order = 'reverse'
        for criterion in topic.listCriteria():
            if criterion.meta_type == 'ATSortCriterion':
                sort_on = criterion.getCriteriaItems()[0][1]
                if len(criterion.getCriteriaItems()) == 2 and sortorder == None:
                    sort_order = criterion.getCriteriaItems()[1][1]
        if sort_on:
            query['sort_on'] = sort_on
        if sort_order:
            query['sort_order'] = sort_order

        #logger.debug(query)
        #results = catalog( ** query)

        #return {'results': results, 'size': batch_size, 'start': batch_start, 'num_results': len(results)}
        return query;

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
        return years


class RecentPublicationsView(View):

    template = ViewPageTemplateFile('templates/collection_view_recent_publications.pt');

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.duplicates = {}
        self.items = []

    def __call__(self):
        self.gutil = getUtility(IProductsGEMIUtility)
        return self.template();

    def getQuery(self):
        query = super(RecentPublicationsView, self).getQuery();
        query['path'] = {"query": "/"}
        return query;

    def getResults(self, b_start=None):
        query = self.getQuery();
        b_start = b_start or self.request.get('b_start', 0);
        b_size = self.context.b_size;
        #limit = self.context.limit;

        results = self.context.queryCatalog(batch=True, b_start=b_start, b_size=b_size, **query)
        acquired_objects = [result.getObject() for result in results];
        for brain in results:
            id = brain.UID;
            if id in self.duplicates:
                continue;
            self.items.append(brain)
            if (len(self.items) >= b_size):
                break;

            is_duplicate, matches = self.gutil.isDuplicate(self, brain.getObject(), 'global', acquired_objects);
            if (is_duplicate):
                for match in matches:
                    self.duplicates[match.UID()] = None

        if results and len(self.items) < b_size:
            self.getResults(b_start + b_size)

        return self.items;

    def getEnableDuplicatesManager(self):
        return True;



def isApplicableCollectionView(view, types):
    return True;

#    if IATTopic.providedBy(view.context):
#        items = view.context.queryCatalog({'portal_type': types}, batch=True, b_size=3)
#    else:
#        items = view.context.results(b_start=0, b_size=3, custom_query={'portal_type': types});

#    if (items is not None):
#        for brain in items:
#            if (not brain.portal_type in types):
#                return False
#        return True

#    return False;
