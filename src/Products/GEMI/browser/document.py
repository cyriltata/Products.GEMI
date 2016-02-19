from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Acquisition import aq_inner
from zope.component import getMultiAdapter
import logging
import re
import lxml.html
from lxml.cssselect import CSSSelector

class SlugView(BrowserView):

    template = ViewPageTemplateFile("templates/document_slug_view.pt")
    
    slugTemplate = "{{{external_content=%s}}}"
    
    content = ""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.logger = logging.getLogger('Products.GEMI::SlugView')
        self.parseSlugs(self.context.CookedBody())
        return self.template();

    def parseSlugs(self, content):
        regex = '{{{external_content=(.*?)}}}'
        compiled_regex = re.compile(regex)
        paths =  compiled_regex.findall(content);
        self.content = self.parsePaths(paths, content)

    def parsePaths(self, paths, content):
        if len(paths) <= 0:
            return content

        for path in paths:
            try:
                slug = self.getFullSlugFromId(path)
                object = self.context.restrictedTraverse(path)
                view = self.getView(object, self.request, object.getLayout())
                view_html = view.__call__();
                content = content.replace(slug, self.getContentCore(view_html))
            except Exception as e:
                self.logger.warn(e)
                content = content.replace(slug, "")

        return content

    def getFullSlugFromId(self, id):
        return self.slugTemplate % id

    def getView(self, context, request, name):
        """
        context = aq_inner(context)
        view = getMultiAdapter((context, request), name=name)
        view = view.__of__(context)
        return view"""
        """ Return a view associated with the context and current HTTP request.

        @param context: Any Plone content object.
        @param name: Attribute name holding the view name.
        """

        try:
            view = context.unrestrictedTraverse("@@" + name)
        except AttributeError:
            try:
                view = context.unrestrictedTraverse(name)
            except AttributeError:
                raise RuntimeError("Instance %s did not have view %s" % (str(context), name))

        view = view.__of__(context)

        return view
    
    def getContentCore(self, html):
        """
        Parse the html and get the contents of the div item ".content-core"
        """
        tree = lxml.html.fromstring(html)
        sel = CSSSelector('div#content-core')
        results = sel(tree)
        try:
            return lxml.html.tostring(results[0]);
        except Exception as e:
            self.logger.warn(e)
            return ''


