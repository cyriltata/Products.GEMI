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
from zope.component import getUtility
from plone.batching import Batch

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
        b_size = 200

        if IATTopic.providedBy(self.context):
            query = self.getQuery()
            query.update(self.getTopicQuery())
            results = self.context.portal_catalog(**query);
            return Batch(results, b_size, b_start, orphan=0)
        else:
            return self.context.results(b_start=b_start, custom_query=query)

    security.declareProtected(View, 'getQuery')
    def getQuery(self):
        query = {
            'sort_on': 'publication_year',
            'sort_order': 'reverse',
            'Language': 'all',
        };

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
