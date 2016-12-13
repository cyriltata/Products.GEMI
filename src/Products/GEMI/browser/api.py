# -*- coding: utf-8 -*
from Products.Five.browser import BrowserView
from Products.GEMI import _
from dateutil.parser import parse as parse_date
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

    def __call__(self):
        if (self.request["REQUEST_METHOD"] == "GET"):
            self.request.response.setHeader("Content-type", "application/json; charset=utf-8")
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
        filter = {
            "show_excluded_from_nav": True,
            "portal_type": ('News Item', 'Event'),
            "review_state": "published",
            "path": {"query": self.request.get("path", "/")}
        }
        

        # Read the first index of the selected batch parameter as HTTP GET request query parameter
        start = self.request.get("b_start", 0)
        limit = 50

        data = {
          "events": {
            "title": _(u"Events"),
            "items": [],
        }, "news": {
            "title": _(u"News"),
            "items": [],
        }}

        items = self.query(start, limit, filter)
        for brain in items:
            obj = brain.getObject();
            if obj.portal_type == "Event":
                data["events"]["items"].append(self.getDataFromEventObject(obj))
            else:
                data["news"]["items"].append(self.getDataFromNewsItemObject(obj))

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
            "contact_name": obj.contact_name(),
            "contact_email": obj.contact_email(),
        }
    
    def getDataFromNewsItemObject(self, obj):
        return  {
            "id": obj.getId(),
            "type": obj.portal_type,
            "title": obj.Title(),
            "headline": obj.Description(),
            "url": obj.absolute_url(),
            "start_or_created": self.formatDate(obj.EffectiveDate()) or self.formatDate(obj.created()),
            "end_or_expires": self.formatDate(obj.ExpirationDate()) or self.formatDate(obj.expires()),
            "location": None,
            "contact_name": obj.Creator(),
            "contact_email": None,
        }
    
    def formatDate(self, date):
        if date is None or date == "None":
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

        return "%s-%s-%s %s:%s:00" % (y, m, d, hr, min)
