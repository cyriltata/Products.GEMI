from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.GEMI.config import *
from zope.interface import implements
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFBibliographyAT.config import FOLDER_TYPES
from bibliograph.core.utils import _decode
from operator import and_

class ProductsGEMIUtility:

    implements(IProductsGEMIUtility)

    cache = {}

    def getBibFolderCategories(self, obj, add = False):
        l = []
        n = self.getBibFolderCategoryCount(obj)+1;
        for i in range(1, n):
            k = BFV_CATEGORY % i
            if obj.hasProperty(k):
                l += [{
                        'id': k,
                        'category': obj.getProperty(k),
                        'reftypes': obj.getProperty(BFV_CATEGORY_REFTYPES % i),
                        'description': obj.getProperty(BFV_CATEGORY_DESCRIPTION % i, []),
                        'tags': obj.getProperty(BFV_CATEGORY_TAGS % i, [])
                    }]

        if not l or add == True:
            l.append(self.defaultCategory(obj));

        return l

    def getBibFolderCategoryCount(self, obj):
        n = obj.getProperty(BFV_CATEGORY_COUNT);
        if (n is None):
            n = 0;
        return n

    def defaultCategory(self, obj):
        i = self.getBibFolderCategoryCount(obj) + 1;
        return {'id': BFV_CATEGORY % i, 'category': '', 'description': '', 'reftypes': [], 'tags': []}

    def saveBibFolderCategorySettings(self, obj, category, index):
        change_properties = {}
        for property_key, property_object in category.iteritems():
            if (obj.hasProperty(property_key)):
                change_properties[property_key] = property_object['value']
            else:
                obj.manage_addProperty(id=property_key, type=property_object['type'], value=property_object['value'])
        if change_properties:
            obj.manage_changeProperties(change_properties);

        if (obj.hasProperty(BFV_CATEGORY_COUNT)):
            obj.manage_changeProperties({BFV_CATEGORY_COUNT: index})
        else:
            obj.manage_addProperty(id=BFV_CATEGORY_COUNT, type='int', value=index)

    def deleteBibFolderCategory(self, obj, ids):
        n = self.getBibFolderCategoryCount(obj);
        del_count = len(ids);
        if (del_count > n + 1):
            raise ValueError, "Can't delete more categories than saved"

        for property in ids:
            if not obj.hasProperty(property):
                return;

        try:
            list = ids + [x + '_reftypes' for x in ids] + [x + '_description' for x in ids] + [x + '_tags' for x in ids];
            obj.manage_delProperties(list);
            if (del_count == n):
                obj.manage_changeProperties({BFV_CATEGORY_COUNT: 0})
        except:
            pass

    def reIndexBibFolderCategories(self, obj):
        categories = self.getBibFolderCategories(obj);
        save = [];
        delete = [];

        # clear index  by deleting all
        n = 1
        for c in categories:
            if obj.hasProperty(c['id']):
                delete.append(c['id'])
                save.append({
                    BFV_CATEGORY % n            : {'value': c['category'], 'type': 'string'},
                    BFV_CATEGORY_DESCRIPTION % n: {'value': c['description'], 'type': 'text'},
                    BFV_CATEGORY_REFTYPES % n  : {'value': c['reftypes'], 'type': 'lines'},
                    BFV_CATEGORY_TAGS % n       : {'value': c['tags'], 'type': 'lines'}
                });
                n += 1;

        if delete:
            self.deleteBibFolderCategory(obj, delete);
        obj.manage_changeProperties({BFV_CATEGORY_COUNT: 0});

        # re-add
        index = 1
        for c in save:
            self.saveBibFolderCategorySettings(obj, c, index);
            index += 1;

    def saveBibFolderFilterSettings(self, obj, settings):
        for key in settings:
            setting = settings[key]
            if obj.hasProperty(key):
                obj.manage_changeProperties({key: setting['value']})
            else:
                obj.manage_addProperty(type=setting['type'], id=key, value=setting['value'])

    def getBibFolderFilterSettings(self, obj):
        return {
            'filter_show' : obj.getProperty(BFV_FILTER_SHOW),
            'filter_by_year' : obj.getProperty(BFV_FILTER_BY_YEAR),
            'filter_authors' : obj.getProperty(BFV_FILTER_AUTHORS, []),
            'filter_years' : obj.getProperty(BFV_FILTER_YEARS, []),
            'filter_default_year': obj.getProperty(BFV_FILTER_DEFAULT_YEAR, ''),
            'filter_default_author': obj.getProperty(BFV_FILTER_DEFAULT_AUTHOR, ''),
            'show_folder_in_collection': obj.getProperty(BFV_SHOW_FOLDER_IN_COLLECTION, 0),
        }

    def getBibFolderFilterValues(self, items):
        authors = filter(None, items.get('filter_authors', '').splitlines());
        authors.sort();
        years = filter(None, items.get('filter_years', '').splitlines());
        years.sort();

        return {
            BFV_FILTER_SHOW : {'type':'int', 'value': int(items.get('filter_show', False) == 'True')},
            BFV_FILTER_BY_YEAR : {'type':'int', 'value': int(items.get('filter_by_year', False) == 'True')},
            BFV_FILTER_AUTHORS : {'type':'lines', 'value': authors},
            BFV_FILTER_YEARS : {'type':'lines', 'value': years},
            BFV_FILTER_DEFAULT_YEAR: {'type': 'string', 'value': items.get('filter_default_year', '')},
            BFV_FILTER_DEFAULT_AUTHOR: {'type': 'string', 'value': items.get('filter_default_author', '')},
            BFV_SHOW_FOLDER_IN_COLLECTION: {'type':'int', 'value': int(items.get('show_folder_in_collection', False) == 'True')}
        };
        
    def groupBibItemsByYears(self, list):
        # nimmt eine liste von References (oder Brains!), gibt ein dictionary zurueck, in dem der key das jahr ist
        # und zu jedem key die liste der references in diesem jahr gehoert
        res = {}
        for r in list:
            year = r.publication_year
            if not res.has_key(year):
                res[year] = [r]
            else: 
                res[year].append(r)
        
        # Now sort each year group by first author
        
        return self.sortByFirstAuthor(res, False)
    
    def sortByFirstAuthor(self, res, plain):
        if plain:
            #res = sorted(res, key=lambda item: (item.getObject().getAuthors()[0].get('lastname'), item.getObject().getAuthors()[0].get('firstname')))
            res = sorted(res, cmp=sort_by_authors);
        else:
            for year, group in enumerate(res):
                #res[group] = sorted(res[group], key=lambda item: (item.getObject().getAuthors()[0].get('lastname'), item.getObject().getAuthors()[0].get('firstname')))
                res[group] = sorted(res[group], cmp=sort_by_authors);

        return res

    def getStartEnd(self, topic, criterion, catalog):
        '''
        Get start and end date ranges for old style plone collections
        '''
        if criterion.meta_type in ['ATDateRangeCriterion']:
            start_date = criterion.getStart()
            end_date = criterion.getEnd()
        elif criterion.meta_type in ['ATFriendlyDateCriteria']:
            date_base = criterion.getCriteriaItems()[0][1]['query']
            if date_base==None:
                date_base = DateTime()
            date_limit = self.getDateLimit(topic, criterion, catalog)
            start_date = min(date_base, date_limit)
            end_date =  max(date_base, date_limit)

        return start_date, end_date

    def getDateLimit(self, topic, criterion, catalog):
        '''
        get the earliest/latest date that should be included in
        a daterange covering all dates defined by the criteria
        '''
        query = topic.buildQuery()
        query['sort_on'] = criterion.Field()
        query['sort_limit'] = 1

        if criterion.getOperation() == 'less':
            query['sort_order'] = 'ascending'
            adjust = -1
        else:
            query['sort_order'] = 'descending'
            adjust = 1
            
        query.pop(criterion.Field())
        results = catalog(**query)
        if len(results) > 0:
            date_limit = results[0][criterion.Field()] + adjust
        else:
            date_limit = DateTime()
        return date_limit

    def isDuplicate(self, context, bibref_item, span_of_search=None, acquired_objects=None):
        """
        checks if bib folder entry is duplicated
        """

        span_of_search = span_of_search or 'global'
        bib_tool = getToolByName(context, 'portal_bibliography')
        all_criteria = bib_tool.getSelectedCriteria()
        entry = bib_tool.getEntryDict(bibref_item)
        ref_types = bib_tool.getReferenceTypes()
        have = all_criteria.has_key
        global_tests = []
        filter = {'portal_type': ref_types}

        # get search span from criteria
        cache_key = 'CMFBibliographyAT_duplicates_cache'
        if acquired_objects is not None:
            self.cache[cache_key] = acquired_objects;

        if cache_key in self.cache:
            acquired_objects = self.cache[cache_key]
        elif span_of_search == 'local':
            # local configuration
            acquired_objects = context.contentValues(filter=filter)
            self.cache[cache_key] = acquired_objects
        elif span_of_search == 'global':
            acquired_objects = []
            portal_catalog = getToolByName(context, 'portal_catalog')
            all_folders = portal_catalog.searchResults({'path': {'query': '/'}, 'meta_type': FOLDER_TYPES, 'Language': 'all'})
            #all_folders = portal_catalog(meta_type=FOLDER_TYPES, path={'query': '/'})
            for each_result in all_folders:
                obj = each_result.getObject()
                acquired_objects += obj.contentValues(filter=filter)
            self.cache[cache_key] = acquired_objects
        else:
            raise ValueError("span of search for duplicates has an invalid value : %s" % span_of_search)

        bibref_item_uid = bibref_item.UID()

        for existing_object in acquired_objects:
            if existing_object.UID() == bibref_item_uid:
                continue
            bib_type = entry.get('reference_type', 'ArticleReference')
            if not have(bib_type):
                continue
            criteria = all_criteria[bib_type]
            if not criteria:
                return False, []
            # authors need special treatment
            for attribute in criteria:
                # authors need special treatment
                if attribute == 'authors':
                    equal = self.compareAuthors(entry, existing_object)
                    if not equal:
                        break
                else:
                    x = entry.get(attribute, None)
                    try:
                        get_func = getattr(existing_object, 'get' + attribute.capitalize())
                    except AttributeError:
                        try:
                            get_func = getattr(existing_object, attribute.capitalize())
                        except AttributeError:
                            # XXX print ?
                            print "can't do get" + attribute.capitalize(), 'or', attribute.capitalize()
                            break;
                    y = _decode(get_func())
                    if y and y[-1] == '.':
                        y = y[:-1]
                    if x and x[-1] == '.':
                        x = x[:-1]
                    if x != y:
                        #print "***Debug***: found difference"
                        #print "%s doesn't match %s" % (x, y)
                        break
            else:
                global_tests.append((True, existing_object))

        matching_objects = [ext_obj for (test, ext_obj) in global_tests if test]
        global_bools = [test for (test, ext_obj) in global_tests]
        if global_tests:
            return reduce(and_, global_bools), matching_objects
        return False, []

    def compareAuthors(self, entry, existing):
        new_last_names = [_decode(a.get('lastname'))
                          for a in entry.get('authors', [])]
        old_last_names = [_decode(a.get('lastname'))
                          for a in existing.getRawAuthors()]
        if new_last_names == old_last_names:
            return True
        return False
    
    def publicationYearQueryValue(self, year):
        year = year.lower().strip();

        if year == 'in press':
            return {'query': ('in press', 'In Press', 'In press'), 'operator': 'or'}
        elif year == 'accepted':
            return {'query': ('accepted', 'Accepted'), 'operator': 'or'}

        return year;
    
def sort_by_authors(item1, item2):
    item1 = item1.getObject();
    item2 = item2.getObject();
    if not hasattr(item1, 'getAuthors') or not hasattr(item2, 'getAuthors'):
        return 0;

    item1Authors = item1.getAuthors();
    item2Authors = item2.getAuthors();
    check = True;
    index1 = 0;
    index2 = 0;
    compared = 0;
    while check and index1 < len(item1Authors) and index2 < len(item2Authors):
        author1 = (item1Authors[index1].get('lastname'), item1Authors[index1].get('firstname'));
        author2 =  (item2Authors[index2].get('lastname'), item2Authors[index2].get('firstname'));
        compared = cmp(author1, author2)
        if (compared == 0):
            index1 += 1;
            index2 += 1;
            # check if one of the items have exahausted it's authors list and return the one with fewer authors as "less-than"
            if index1 >= len(item1Authors) and index1 < len(item2Authors):
                compared = -1
                check = False;
            if index2 >= len(item2Authors) and index2 < len(item1Authors):
                compared = 1
                check = False;
        else:
            check = False

    return compared;
        