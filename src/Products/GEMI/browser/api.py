# -*- coding: utf-8 -*
from Products.Five.browser import BrowserView
from dateutil.parser import parse as parse_date
from DateTime import DateTime
from datetime import datetime
from Products.CMFCore.utils import getToolByName

try:
    import json
except ImportError:
    # Python 2.5/Plone 3.3 use simplejson
    import simplejson as json

class ExportNewsAndEventsAsJSON(BrowserView):
    """Export News and Event content types in a JSON."""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.members = {};

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "GET"):
            self.request.response.setHeader("Content-type", "application/json; charset=utf-8")
            self.request.response.setHeader("Access-Control-Allow-Origin", "*")
            return json.dumps(self.getItems());

    
    def query(self, start, limit, contentFilter):
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
        # mtool = self.context.portal_membership
        cur_path = '/'.join(self.context.getPhysicalPath())
        path = {}

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
        show_inactive = True;#mtool.checkPermission('Access inactive portal content', self.context)
        contents = self.context.portal_catalog(contentFilter, show_all=1, show_inactive=show_inactive,)

        # remove contents exluded from navigation if asked for
        filtered = []
        if not contentFilter['show_excluded_from_nav']:
            for brain in contents:
                if (not getattr(brain, 'exclude_from_nav', False)):
                    filtered.append(brain);
        else:
            filtered = contents

        from Products.CMFPlone import Batch
        return Batch(filtered, b_size, b_start, orphan=0)

    def getItems(self):
        # Read the first index of the selected batch parameter as HTTP GET request query parameter
        start = self.request.get("b_start", 0)
        limit = self.request.get("b_limit", 20)

        filter = {
            "show_excluded_from_nav": True,
            "review_state": "published",
            "path": {"query": self.request.get("path", "/")}
        }

        date_range = self.getDateRangeQuery(
            self.request.get('date', None),
            self.request.get('from', None),
            self.request.get('to', None)
        );
        
        #effective_date = self.getDateRangeQuery('today', None, None);
        filter['effectiveRange'] = DateTime();

        portal_type = self.request.get('type', 'Event');
        filter['portal_type'] = (portal_type,)

        if (date_range is not None and portal_type == 'Event'):
            filter['portal_type'] = ('Event',)
            filter['end'] = date_range
        elif (date_range is not None and portal_type == 'NewsItem'):
            filter['portal_type'] = ('News Item',)
            filter['expires'] = date_range #should I use last modified time or created date for news item?
        elif (portal_type == 'NewsItem'):
            filter['portal_type'] = ('News Item',)
            filter['sort_on'] = 'Date',
            filter['sort_order'] = 'reverse',
            filter['sort_limit'] = limit
        else:
            raise Exception("Request parameters not understood. A date or date range is required!")

        data = {
            'timezone': 'CET',
            'items': [],
        }

        items = self.query(start, limit, filter)
        for brain in items:
            obj = brain.getObject();
            if obj.portal_type == "Event":
                data['items'].append(self.getDataFromEventObject(obj))
            else:
                data['items'].append(self.getDataFromNewsItemObject(obj))

        return data
    
    def getDataFromEventObject(self, obj):
        return  {
            "id": obj.getId(),
            "type": obj.portal_type,
            "title": obj.Title(),
            "headline": None,
            "url": obj.absolute_url(),
            "start_or_created": self.formatDate(obj.start()) or self.formatDate(obj.EffectiveDate()) or self.formatDate(obj.created()),
            "end_or_expires": self.formatDate(obj.end()) or self.formatDate(obj.ExpirationDate()) or self.formatDate(obj.expires()),
            "location": obj.location,
            "contact_name": obj.contact_name() or self.getMemberById(obj.Creator()) or obj.Creator(),
            "contact_email": obj.contact_email(),
            "modified": self.formatDate(obj.modified()),
        }
    
    def getDataFromNewsItemObject(self, obj):
        return  {
            "id": obj.getId(),
            "type": obj.portal_type,
            "title": obj.Title(),
            "headline": obj.Description(),
            "url": obj.absolute_url(),
            "start_or_created":  self.formatDate(obj.modified()) or self.formatDate(obj.EffectiveDate()),
            "end_or_expires": self.formatDate(obj.expires()) or self.formatDate(obj.ExpirationDate()),
            "location": None,
            "contact_name": self.getMemberById(obj.Creator()) or obj.Creator(),
            "contact_email": None,
            "modified": self.formatDate(obj.modified()),
        }
    
    def formatDate(self, date, f=None):
        if date is None or date == "None" or type(date) is None:
            return None
        if type(date) is str:
            #format: 2016-12-10T07:00:00+01:00
            date = parse_date(date);
            y = date.year
            m = format(date.month, '02')
            d = format(date.day, '02')
            hr = format(date.hour, '02')
            min = format(date.minute, '02')
        else:
            y = date.year()
            m = format(date.month(), '02')
            d = format(date.day(), '02')
            hr = format(date.hour(), '02')
            min = format(date.minute(), '02')
            
        if (f is None):
            f = "%s.%s.%s %s:%s:00";

        return  f % (y, m, d, hr, min)

    def getDateRangeQuery(self, date_str, date_from, date_to):
        tz= 'CET';
        z = DateTime(tz);
        min_date = None;
        max_date = None;

        if (date_str is not None):
            if (date_str == 'today'):
                min_date = ("%s.%s.%s 00:00:01 %s") % (z.day(), z.month(), z.year(), tz);
                max_date = ("%s.%s.%s 23:59:59 %s") % (z.day(), z.month(), z.year(), tz);
            elif (date_str == 'yesterday'):
                y = z - 1
                min_date = ("%s.%s.%s 00:00:01 %s") % (y.day(), y.month(), y.year(), tz);
                max_date = ("%s.%s.%s 23:59:59 %s") % (y.day(), y.month(), y.year(), tz);
            elif (date_str == 'tomorrow'):
                y = z + 1
                min_date = ("%s.%s.%s 00:00:01 %s") % (y.day(), y.month(), y.year(), tz);
                max_date = ("%s.%s.%s 23:59:59 %s") % (y.day(), y.month(), y.year(), tz);
            else:
                self.validateDateText(date_str);
                min_date = ("%s 00:00:01 %s") % (date_str, tz);
                max_date = ("%s 23:59:59 %s") % (date_str, tz);

        if (date_from is not None and date_to is not None):
            self.validateDateText(date_from);
            self.validateDateText(date_to);
            min_date = ("%s 00:00:01 %s") % (date_from, tz);
            max_date = ("%s 23:59:59 %s") % (date_to, tz);

        if (min_date is None or max_date is None):
            return None;

        date_range = {
            'query': (
                DateTime(min_date, datefmt='international'),
                DateTime(max_date, datefmt='international'),
            ),
            'range': 'min:max',
        }
        return date_range;

    def validateDateText(self, date_text):
        try:
            datetime.strptime(date_text, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Incorrect data format, should be DD.MM.YYYY")
    
    def getMemberById(self, id):
        if (id not in self.members):
            portal_membership = getToolByName(self.context, 'portal_membership');
            member = portal_membership.getMemberById(id)
            self.members[id] = member.getProperty("fullname")

        return self.members.get(id, None);

