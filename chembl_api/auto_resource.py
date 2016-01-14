__author__ = 'mnowotka'

import tastypie.resources as res
from tastypie import fields
from chembl_api.base_resource import ChemblBaseModelResource
from chembl_api.blob_field import BlobField

#-----------------------------------------------------------------------------------------------------------------------

class ChemblModelResource(ChemblBaseModelResource):

#-----------------------------------------------------------------------------------------------------------------------

    @classmethod
    def api_field_from_django_field(cls, f, default=fields.CharField):
        """
        Returns the field type that would likely be associated with each
        Django type.
        """
        if f.get_internal_type() == 'BlobField':
            return BlobField
        if f.get_internal_type() == 'ForeignKey':
            return fields.ForeignKey
        if f.get_internal_type() == 'ManyToManyField':
            return fields.ManyToManyField
        if f.get_internal_type() == 'OneToOneField':
            return fields.OneToOneField

        return super(ChemblModelResource, cls).api_field_from_django_field(f, default)

#-----------------------------------------------------------------------------------------------------------------------

    @classmethod
    def get_fields(cls, fields=None, excludes=None):
        """
        Given any explicit fields to include and fields to exclude, add
        additional fields based on the associated model.
        """
        final_fields = {}
        fields = fields or []
        excludes = excludes or []

        if not cls._meta.object_class:
            return final_fields

        for f in cls._meta.object_class._meta.fields:
            # If the field name is already present, skip
            if f.name in cls.base_fields:
                continue

            # If field is not present in explicit field listing, skip
            if fields and f.name not in fields:
                continue

            # If field is in exclude list, skip
            if excludes and f.name in excludes:
                continue

            if cls.should_skip_field(f):
                continue

            api_field_class = cls.api_field_from_django_field(f)

            kwargs = {
                'attribute': f.name,
                'help_text': f.help_text,
            }

            if f.null is True:
                kwargs['null'] = True

            if f.blank is True:
                kwargs['blank'] = True

            kwargs['unique'] = f.unique

            if not f.null and f.blank is True:
                kwargs['default'] = ''

            if f.get_internal_type() == 'TextField':
                kwargs['default'] = ''

            if f.has_default():
                kwargs['default'] = f.default

            if getattr(api_field_class, 'is_related', False):
                name = res.__name__ + "." + f.related.parent_model.__name__ + "Resource"
                #if f.related.parent_model == f.related.model:
                #    name = 'self'
                final_fields[f.name] = api_field_class(name, **kwargs)

            else:
                final_fields[f.name] = api_field_class(**kwargs)

            final_fields[f.name].instance_name = f.name

        return final_fields

#-----------------------------------------------------------------------------------------------------------------------

    @classmethod
    def should_skip_field(cls, field):
        return False

#-----------------------------------------------------------------------------------------------------------------------