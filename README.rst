.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide_addons.html
   This text does not appear on pypi or github. It is a comment.

==============================================================================
Products.GEMI
==============================================================================

Plone add-on for GEMI specific wishes.

Features
--------

- Collections for Products.CMFBibliographyAT content types
- Overwrite plone translations
- Folder view with items excluded from navigation not shown
- etc..

Translations
------------

This product has been translated into

- English
- German


Installation
------------

Install Products.GEMI by adding it to your buildout::

    [buildout]

    ...

    eggs =
        Products.GEMI

    ....
    
    zcml =
        Products.GEMI



and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/cyriltata/Products.GEMI/issues
- Source Code: https://github.com/cyriltata/Products.GEMI
- Documentation: https://github.com/cyriltata/Products.GEMI/README.rst


Support
-------

If you are having issues, please let us know at: ctata@gwdg.de


License
-------

The project is licensed under the GPLv2.
