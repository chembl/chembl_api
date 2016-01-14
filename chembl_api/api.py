__author__ = 'mnowotka'

import sys
import inspect
import tastypie.resources as res
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.throttle import BaseThrottle
from tastypie.paginator import Paginator
from tastypie.api import Api
import chembl_business_model.models as models
from chembl_api.compound_table_resource import CompoundTableResource
from chembl_api.auto_resource import ChemblModelResource
from chembl_api.compound_records_detailed_resource import CompoundRecordsDetailedResource

#-----------------------------------------------------------------------------------------------------------------------

def getFilters(fields):
    ret = {}
    for field in fields:
        if not getattr(field, 'rel'):
            ret[field.name] = ALL
        else:
            ret[field.name] = ALL_WITH_RELATIONS
    return ret

#-----------------------------------------------------------------------------------------------------------------------

def createMetaClass(modelClass):
    return type("Meta", (object,),
        {"queryset": modelClass.objects.all(), "excludes": modelClass.api_exclude,
         "authentication": SessionAuthentication(), "authorization": DjangoAuthorization(),
         "filtering": getFilters(modelClass._meta.fields),
         "ordering": [str(field.name) for field in modelClass._meta.fields],
         "throttle": BaseThrottle(throttle_at=100), "paginator_class": Paginator})

#-----------------------------------------------------------------------------------------------------------------------

def createModelResourceClass(modelClass):
    defaultIndex = 'pk'
    if hasattr(modelClass, 'defaultIndex'):
        defaultIndex = modelClass.defaultIndex

    dict = {"Meta": createMetaClass(modelClass), "defaultIndex": defaultIndex}

    return type(modelClass.__name__ + "Resource", (ChemblModelResource, ), dict)

#-----------------------------------------------------------------------------------------------------------------------

def getModelClasses(module):
    return  [x[1] for x in inspect.getmembers(sys.modules[module.__name__]) if
             inspect.isclass(x[1]) and hasattr(x[1], 'api_exclude')]

#-----------------------------------------------------------------------------------------------------------------------

def createResourceClassesFrom(module):
    for cls in getModelClasses(module):
        yield createModelResourceClass(cls)

#-----------------------------------------------------------------------------------------------------------------------

api = Api(api_name='v1')

for resource in createResourceClassesFrom(models):
    setattr(sys.modules[res.__name__], resource.__name__, resource)
    api.register(resource())

api.register(CompoundTableResource())
api.register(CompoundRecordsDetailedResource())

#-----------------------------------------------------------------------------------------------------------------------
