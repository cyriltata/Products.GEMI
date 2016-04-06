from Products.GEMI.interfaces import IProductsGEMIUtility
from Products.GEMI.config import *
from zope.interface import implements

class ProductsGEMIUtility:

    implements(IProductsGEMIUtility)

    def getBibFolderCategories(self, obj, add = False):
        l = []
        n = self.getBibFolderCategoryCount(obj)+1;
        for i in range(1, n):
            k = BFV_CATEGORY % i
            if obj.hasProperty(k):
                l += [{'id': k, 'category': obj.getProperty(k), 'reftypes': obj.getProperty(BFV_CATEGORY_REFTYPES % i)}]

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
        return {'id': BFV_CATEGORY % i, 'category': '', 'reftypes': []}

    def addBibFolderCategory(self, obj, name, reftypes):
        if not name or not reftypes:
            return;

        n = self.getBibFolderCategoryCount(obj) + 1;
        obj.manage_addProperty(type='string', id=BFV_CATEGORY % n, value=name)
        obj.manage_addProperty(type='lines', id=BFV_CATEGORY_REFTYPES % n, value=reftypes)
        if (obj.hasProperty(BFV_CATEGORY_COUNT)):
            obj.manage_changeProperties({BFV_CATEGORY_COUNT: n})
        else:
            obj.manage_addProperty(type='int', id=BFV_CATEGORY_COUNT, value=1)

    def modifyBibFolderCategory(self, obj, n, name, reftypes):
        if not name or not reftypes:
             return;

        obj.manage_changeProperties({BFV_CATEGORY % n: name, BFV_CATEGORY_REFTYPES % n: reftypes})
        if (not obj.hasProperty(BFV_CATEGORY_COUNT)):
            obj.manage_addProperty(type='int', id=BFV_CATEGORY_COUNT, value=1)


    def deleteBibFolderCategory(self, obj, ids):
        n = self.getBibFolderCategoryCount(obj);
        del_count = len(ids);
        if (del_count > n):
            raise ValueError, "Can't delete more categories than saved"
        
        for property in ids:
            if not obj.hasProperty(property):
                return;

        list = ids + [x + '_reftypes' for x in ids];
        obj.manage_delProperties(list);
        if (del_count == n):
            obj.manage_changeProperties({BFV_CATEGORY_COUNT: 0})

    def reIndexBibFolderCategories(self, obj):
        categories = self.getBibFolderCategories(obj);
        save = [];
        delete = [];

        # clear index  by deleting all
        for c in categories:
            if obj.hasProperty(c['id']):
                delete.append(c['id'])
                save.append(c);

        if delete:
            self.deleteBibFolderCategory(obj, delete);
        obj.manage_changeProperties({BFV_CATEGORY_COUNT: 0});

        # re-add
        for c in save:
            self.addBibFolderCategory(obj, c['category'], c['reftypes'])
    
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
        }
        
    def groupBibItemsByYears(self, list):
        # nimmt eine liste von References (oder Brains!), gibt ein dictionary zurueck, in dem der key das jahr ist
        # und zu jedem key die liste der references in diesem jahr gehoert
        res = {}
        for r in list:
            year = r.publication_year
            if not res.has_key(year):
                res[year] = [r]
            else: res[year].append(r)
        return res
        
        