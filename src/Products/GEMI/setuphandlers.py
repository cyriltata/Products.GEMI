# -*- coding: utf-8 -*-
import logging

def post_install(context):
    """Post install script"""
    if context.readDataFile('productsgemi_default.txt') is None:
        return
    # Do something during the installation of this package
    # define_indexes(context)
    # update_catelog(context, False)

def define_indexes(context):
    portal = context.getSite()
    logger = logging.getLogger('Products.GEMI::define_indexes')
    catalog = getToolByName(portal, 'portal_catalog')
    indexes = catalog.indexes()

    # Specify the indexes you want, with ('index_name', 'index_type')
    wanted = (('publication_year', 'FieldIndex'),)

    indexables = []
    for name, meta_type in wanted:
        if name not in indexes:
            catalog.addIndex(name, meta_type)
            indexables.append(name)
            logger.info("Added %s for field %s.", meta_type, name)
    # lines below if you want also reindex items when executing it
    if len(indexables) > 0:
        logger.info("Indexing new indexes %s.", ', '.join(indexables))
        catalog.manage_reindexIndex(ids=indexables)

def update_catalog(context, clear=True):
    portal = context.getSite()
    logger = logging.getLogger('Products.GEMI::update_catalog')
    logger.info('Updating catalog (with clear=%s) so items in profiles/default/structure are indexed...' % clear )
    catalog = portal.portal_catalog
    err = catalog.refreshCatalog(clear=clear)
    if not err:
        logger.info('...done.')
    else:
        logger.warn('Could not update catalog.')
