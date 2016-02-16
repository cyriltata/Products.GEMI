from Acquisition import aq_inner

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


def typesAsVocabulary():
    site = getSite()
    context = aq_inner(site)
    factory = getUtility(IVocabularyFactory, 'plone.app.vocabularies.ReallyUserFriendlyTypes')
    vocabulary = factory(context)
    return vocabulary

def types():
    vocabulary = typesAsVocabulary()
    types = [{'id': term.value, 'title': term.title} for term in vocabulary]
    return types


