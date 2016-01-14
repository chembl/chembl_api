__author__ = 'mnowotka'

from tastypie.resources import ALL
import chembl_business_model.models as models
from chembl_api.base_resource import ChemblBaseModelResource

#-----------------------------------------------------------------------------------------------------------------------

class TableProperty(ChemblBaseModelResource):
    class Meta:
        queryset = models.CompoundProperties.objects.all()
        resource_name = 'properties'
        fields = ['full_mwt', 'full_molformula']
        ordering = ['full_mwt', 'full_molformula']
        defaultIndex = 'pk'
        include_resource_uri = False
        filtering = {
            "full_mwt" : ALL,
            "full_molformula" : ALL
        }

#-----------------------------------------------------------------------------------------------------------------------
