__author__ = 'mnowotka'

from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.throttle import BaseThrottle
from tastypie.paginator import Paginator
from tastypie import fields
import chembl_business_model.models as models
from chembl_api.base_resource import ChemblBaseModelResource

#-----------------------------------------------------------------------------------------------------------------------

class CompoundRecordsDetailedResource(ChemblBaseModelResource):

    title = fields.CharField('doc__title', null=True, blank=True)
    doc_id = fields.IntegerField('doc__doc_id', null=True, blank=True)
    src_description = fields.CharField('src__src_description', null=True, blank=True)
    molecule = fields.ForeignKey('tastypie.resources.MoleculeDictionaryResource', 'molecule', null=True, blank=True)
    defaultIndex = 'pk'

    class Meta:
        queryset = models.CompoundRecords.objects.all()
        resource_name = 'detailedrecord'
        defaultIndex = 'pk'
        include_resource_uri = True
        ordering = ['compound_key', 'compound_name', 'curated', 'description', 'doc_id', 'filename', 'molecule',
                    'old_compound_key', 'record_id', 'removed', 'resource_uri', 'src_compound_id',
                    'src_compound_id_version', 'title', 'updated_by', 'updated_on']
        filtering = {'compound_key' : ALL,
                     'compound_name' : ALL,
                     'curated' : ALL,
                     'description' : ALL,
                     'doc_id' : ALL,
                     'filename' : ALL,
                     'molecule' : ALL_WITH_RELATIONS,
                     'old_compound_key' : ALL,
                     'record_id' : ALL,
                     'removed' : ALL,
                     'resource_uri' : ALL,
                     'src_compound_id' : ALL,
                     'src_compound_id_version' : ALL,
                     'title' : ALL,
                     'updated_by' : ALL,
                     'updated_on': ALL}
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
        throttle =  BaseThrottle(throttle_at=100)
        paginator_class = Paginator

#-----------------------------------------------------------------------------------------------------------------------
