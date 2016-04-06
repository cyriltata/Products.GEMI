# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from Products.GEMI import _
from zope import schema
from zope.interface import Interface
from zope import schema
from plone.directives import form
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from z3c.form.browser.checkbox import CheckBoxFieldWidget


class IProductsGemiLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

class IGemifolder(Interface):
    """ Dummy content type for package (DO NOT USE) """

    title = schema.TextLine(
        title=_(u"Title"),
        required=True,
    )

    description = schema.Text(
        title=_(u"Description"),
        required=False,
    )
    
class IProductsGEMISettings(form.Schema):
    """ Interface defining the scheme for control panel
        of Products.GEMI extionsion """

    show_collection_filter = schema.Bool(
        title=_(u"show_filter_help", default=u"Show filter in 'Filter view' of collection"),
        description=_(u"show_filter_desc_help", default=u"If selected the filter to search for collections will be shown above listing"),
        required=False,
        default=True
    )

    show_nav_exluded_items = schema.Bool(
        title=_(u"Show items exluded from navigation"),
        description=_(u"help_show_nav_exluded_items", default=u"If selected, contents normally excluded from navigation will not be listed in this view"),
        required=False,
        default=False
    )

    form.widget(allowed_content_types=CheckBoxFieldWidget)
    allowed_content_types = schema.List(
        title=_(u"Enabled content types"),
        description=_(u"help_select_content_types_view", default=u"Select content types that you will want to be shown when view is selected"),
        required=False,
        default=['Folder'],
        value_type=schema.Choice(source="plone.app.vocabularies.ReallyUserFriendlyTypes"),
    )

    
    form.fieldset(
        'foldersettings',
        label=_(u"Folder Content-type View Settings"),
        fields=['show_nav_exluded_items', 'allowed_content_types']
    )
    
    form.fieldset(
        'collectionsettings',
        label=_(u"Collection Filter View Settings"),
        fields=['show_collection_filter']
    )

    

class IStatusMessage:

    klass = None

    def __init__(self, message=None, title=None, type=None):
        self.message = message
        self.title = title
        self.type = type #can be 'info', 'error'
        self.klass = "portalMessage %s" % self.type

    def setMessage(self, message):
        self.message = message

    def setTitle(self, title):
        self.title = title

    def setType(self, type):
        self.type = type
        self.klass = "portalMessage %s" % self.type

class IObject(object):
    pass

class IProductsGEMIUtility(Interface):
    """
    Marker interface for GEMI utility object
    """

