# -*- coding: utf-8 -*-
"""A view module that contains various generic views"""

from Products.GEMI import _
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GEMI.config import *
from Products.GEMI.interfaces import IProductsGEMIUtility
from zope.component import getUtility
from Products.LinguaPlone.interfaces import ITranslatable
from Acquisition import aq_inner
from zope.component import getMultiAdapter

class TranslatedObjectView(BrowserView):

    template = ViewPageTemplateFile("templates/translated_object.pt");
    found_translation = True
    message = None

    def __init__(self, context, request):
        super(TranslatedObjectView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.gutil = getUtility(IProductsGEMIUtility)

    def __call__(self):
        self.initialize();
        return self.template();

    def initialize(self):
        tr_lang = self.get_other_language();
        if (not tr_lang):
            self.content = self.translation_not_found();
        else:
            self.content = self.get_translated_object(tr_lang);

    def current_site_language(self):
        """
        @return: Two-letter string, the active language code
        """
        context = self.context.aq_inner
        portal_state = portal_state = context.unrestrictedTraverse("@@plone_portal_state");
        return portal_state.language()

    def language(self):
        return self.context.aq_inner.Language();

    def get_languages(self):
        portal_languages = self.context.portal_languages

        # Get barebone language listing from portal_languages tool
        langs = portal_languages.getAvailableLanguages()
        return langs.keys();

    def get_other_language(self):
        languages = self.get_languages();
        lang = self.language();
        if (not lang in languages):
            return None

        for l in languages:
            if (l != lang):
                return l;
        return None

    def get_translated_object(self, lang):
        context = aq_inner(self.context);
        if ITranslatable.providedBy(context):
            translated = context.getTranslation(lang)
            if translated:
                return self.get_view(translated)

        return self.translation_not_found();

    def get_view(self, context):
        context = aq_inner(context);
        if self.context.getLayout() == context.getLayout():
            self.message = _('translation_selected_same_view', default=u"The translated content has been assigned the same layout. This might lead to an unpleasant loop.");
            self.found_translation = False;
            return;

        try:
            #view = getMultiAdapter((context, self.request), name=context.getLayout())
            #view = context.unrestrictedTraverse("@@" + context.getLayout())
            #view = view.__of__(context);
            #return view
            return context;
        except Exception as e:
            self.message = _('translation_read_error', default=u"An error occured reading the translated object");
            self.found_translation = False;

    def translation_not_found(self):
        self.message = _('translation_not_found', default=u"A translated version of this object was not found.");
        self.found_translation = False;
        

