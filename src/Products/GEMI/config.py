from Products.GEMI import _

PROJECTNAME = "Products.GEMI"

ALLOWED_TYPES_COLLECTION_FILTER_VIEW = ('ArticleReference',)

ALLOWED_TYPES_CONTENT_TYPE_VIEW = [
    ('Folder',      _(u'Folder')),
    ('Document',    _(u'Page')),
    ('Link',        _(u'Link')),
    ('Image',       _(u'Image')),
    ('Topic',       _(u'Collection')),
    ('Collection',  _(u'Collection (old style)')),
    ('Event',       _(u'Event')),
    ('File',        _(u'File')),
    ('News Item',   _(u'News Item')),
    ('Form Folder', _(u'Form Folder')),
    ('Bibliography Folder', _(u'Bibliography Folder'))
]