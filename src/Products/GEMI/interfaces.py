# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from Products.GEMI import _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IProductsGemiLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class ICollectiveGemiSettings(Interface):
    """ Marker interface for browser views """

class ICollectiveGemiCollection(Interface):
    """ Marker interface for collections """

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
