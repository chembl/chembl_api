__author__ = 'mnowotka'

from tastypie.resources import ALL
import chembl_business_model.models as models
from chembl_api.base_resource import ChemblBaseModelResource

#-----------------------------------------------------------------------------------------------------------------------

class TableStructure(ChemblBaseModelResource):
    class Meta:
        queryset = models.CompoundStructures.objects.all()
        resource_name = 'structure'
        fields = ['canonical_smiles', 'standard_inchi', 'standard_inchi_key']
        ordering = ['canonical_smiles', 'standard_inchi', 'standard_inchi_key']
        defaultIndex = 'pk'
        include_resource_uri = False
        filtering = {
            "canonical_smiles" : ALL,
            "standard_inchi" : ALL,
            "standard_inchi_key" : ALL,
        }

#-----------------------------------------------------------------------------------------------------------------------
