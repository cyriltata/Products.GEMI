from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five.browser import BrowserView
import json
from plone.app.layout.navigation.interfaces import INavigationRoot
from zope.component import getMultiAdapter


class EmbedContentPlugin(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((context, request), name=u"plone")
        
    contents = []
    
    crumbs = []

    def __call__(self):
        limit = 50
        start = self.request.get("b_start", 0)
        path = self.request.get("path", None)
        path_is_parent = int(self.request.get("pip", 0)) == 1
        is_ajax = self.request.get("is_ajax", False)

        if (path is None and is_ajax):
            return ''
        
        if (path is None and not is_ajax):
            path = self.context.getPhysicalPath()

        # @todo validate context
        context = self.context.restrictedTraverse(path)
        if not ISiteRoot.providedBy(context):
            if (path_is_parent):
                context = context.aq_inner
            else:
                context = context.aq_inner.aq_parent

        if IFolderish.providedBy(context):
            self.contents = self.query(context, start, limit)
            self.crumbs = self.getCrumbs(context)

        if (is_ajax):
            return self.printContentsJson();

        return self.index()

    def printContentsJson(self):
        jsondata = {'contents': [], 'crumbs': []}
        for item in self.contents:
            jsondata['contents'].append({
                                        'url': item.absolute_url,
                                        'id': item.id,
                                        'title': item.Title,
                                        'context': item.getPath(),
                                        'isf': item.isPrincipiaFolderish,
                                        'klass': 'portal_content no_selection contenttype-' + self.normalizeString(item.portal_type) + ' state-' + self.normalizeString(item.review_state)
                                        });
            
        for item in self.crumbs:
            jsondata['crumbs'].append({
                                      'title': item.Title(),
                                      'url': item.absolute_url(),
                                      'context': '/'.join(item.getPhysicalPath()),
                                      'isf': 1
                                      })

        pretty = json.dumps(jsondata, sort_keys=True)
        self.request.response.setHeader("Content-type", "application/json")
        return pretty
    
    def query(self, context, start, limit):
        b_size = limit
        b_start = start

        # set to content filter
        mtool = context.portal_membership
        cur_path = '/'.join(context.getPhysicalPath())
        filter = {}
        filter['path'] = {'query': cur_path, 'depth': 1}
        filter['sort_on'] = 'getObjPositionInParent'

        # Folder or Large Folder like content
        show_inactive = mtool.checkPermission('Access inactive portal content', context)
        contents = self.context.portal_catalog(filter, show_all=1, show_inactive=show_inactive, )

        from Products.CMFPlone import Batch
        return Batch(contents, b_size, b_start, orphan=0)

    def normalizeString(self, text):
        return self.plone_view.normalizeString(text);
    
    def getCrumbs(self, object):
        inner = object.aq_inner
        iter = inner
        crumbs = [iter]

        while iter is not None:
            if INavigationRoot.providedBy(iter):
                break

            if not hasattr(iter, "aq_parent"):
                break;

            iter = iter.aq_parent
            crumbs.append(iter)

        return list(reversed(crumbs));

        