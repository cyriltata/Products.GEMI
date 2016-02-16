# -*- coding: utf-8 -*-


def post_install(context):
    """Post install script"""
    if context.readDataFile('productsgemi_default.txt') is None:
        return
    # Do something during the installation of this package

def define_indexes(context):
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
