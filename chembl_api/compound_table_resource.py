__author__ = 'mnowotka'

from tastypie.resources import ALL, ALL_WITH_RELATIONS, convert_post_to_put
from tastypie.authentication import Authentication
from tastypie.authorization import DjangoAuthorization
from tastypie.throttle import BaseThrottle
from tastypie.paginator import Paginator
from tastypie.serializers import Serializer
from tastypie import fields
from django.db.models import Q
import chembl_business_model.models as models
from chembl_api.base_resource import ChemblBaseModelResource
from chembl_api.blob_field import BlobField
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from tastypie.utils import dict_strip_unicode_keys
import json
import re
import csv

from django.http.response import HttpResponseBase
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from tastypie.utils.mime import build_content_type

from django.conf import settings
from tastypie.exceptions import BadRequest
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse


inchi_key_regex = re.compile('[A-Z]{14}-[A-Z]{10}-[A-Z]')

#-----------------------------------------------------------------------------------------------------------------------

class CompoundTableSerializer(Serializer):
    formats = ['json', 'xml', 'sdf', 'csv']

    content_types = {'json': 'application/json',
                     'jsonp': 'text/javascript',
                     'xml': 'application/xml',
                     'sdf': 'chemical/x-mdl-sdfile',
                     'csv': 'text/csv',
                    }

#-----------------------------------------------------------------------------------------------------------------------

class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

#-----------------------------------------------------------------------------------------------------------------------

class CompoundTableResource(ChemblBaseModelResource):

    properties = fields.ToOneField('chembl_api.table_property.TableProperty', 'compoundproperties',
        full=True, null=True, blank=True)
    image = BlobField('compoundimages__png', null=True, blank=True)
    structure = fields.ToOneField('chembl_api.table_structure.TableStructure', 'compoundstructures',
        full=True, null=True, blank=True)
    chembl_id = fields.CharField('chembl__chembl_id')
    defaultIndex = 'pk'

    class Meta:
        queryset = models.MoleculeDictionary.objects.all()
        serializer = CompoundTableSerializer()
        resource_name = 'compound'
        defaultIndex = 'pk'
        include_resource_uri = False
        fields = ['molregno', 'pref_name']
        ordering = ['molregno', 'pref_name', 'properties', 'structure']
        collection_name = 'compounds'
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = DjangoAuthorization()
        throttle =  BaseThrottle(throttle_at=100)
        paginator_class =  Paginator
        filtering = {
            "properties" : ALL_WITH_RELATIONS,
            "structure" : ALL_WITH_RELATIONS,
            "molregno" : ALL,
            "pref_name": ALL
        }
        ordering = ['chembl_id', 'molregno', 'pref_name', 'properties', 'structure']

#-----------------------------------------------------------------------------------------------------------------------

    def get_list(self, request, **kwargs):
        base_bundle = self.build_bundle(request=request)
        search_term = request.GET.get('q', '')
        dt_filters = request.GET.get('filters')
        if dt_filters:
            dt_filters = json.loads(dt_filters)

        search_filters = None
        if search_term:
            if search_term.isdigit():
                search_filters = Q(chembl_id__contains=search_term) | Q(pk=int(search_term))
            elif search_term.isalpha():
                search_filters = Q(pref_name__icontains=search_term)
            elif search_term.isalnum() and search_term.startswith('CHEMBL'):
                search_filters = Q(chembl__pk__startswith=search_term)
            elif inchi_key_regex.match(search_term):
                search_filters = Q(compoundstructures__standard_inchi_key=search_term)
            elif search_term.startswith('InChI='):
                search_filters = Q(compoundstructures__standard_inchi__startswith=search_term)
            elif len(search_term) > 6:
                search_filters = Q(compoundstructures__canonical_smiles__icontains=search_term) | \
                                 Q(compoundstructures__standard_inchi__icontains=search_term) | \
                                 Q(compoundstructures__standard_inchi_key__icontains=search_term)

        objects = self.obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs))

        if dt_filters:
            datatables_filters = self.build_data_tables_filters(filters=dt_filters)
            if datatables_filters:
                objects = objects.filter(datatables_filters)

        if search_filters:
            objects = objects.filter(search_filters)
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        if hasattr(request, 'format') and request.format not in ('sdf', 'csv'):
            paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(),
                limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
            to_be_serialized = paginator.page()

            # Dehydrate the bundles in preparation for serialization.
            bundles = []

            for obj in to_be_serialized[self._meta.collection_name]:
                bundle = self.build_bundle(obj=obj, request=request)
                bundles.append(self.full_dehydrate(bundle, for_list=True))

            to_be_serialized[self._meta.collection_name] = bundles
            to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)

        else:
            to_be_serialized = sorted_objects

        return self.create_response(request, to_be_serialized)


#-----------------------------------------------------------------------------------------------------------------------

    def build_data_tables_filters(self, filters=None):
        ret = None
        logic = None
        if not filters:
            return None
        for filter in filters:
            value = filter.get('value')
            field_name = filter.get('column')
            filter_type = filter.get('operator')
            if value and filter_type and filter_type:
                if not field_name in ["molregno", "chembl_id", "pref_name", "canonical_smiles", "full_molformula",
                                      "standard_inchi", "standard_inchi_key", "full_mwt"]:
                    continue
                if field_name == "molregno":
                    if not filter_type in ['exact', 'range', 'gt', 'gte', 'lt', 'lte', 'in']:
                        continue
                elif field_name == "chembl_id":
                    if not filter_type in ['exact', 'range', 'in']:
                        continue
                elif field_name == "full_mwt":
                    if not filter_type in ['exact', 'range', 'gt', 'gte', 'lt', 'lte', 'in', 'isnull']:
                        continue
                elif not filter_type in ['exact', 'iexact', 'contains', 'icontains', 'istartswith', 'startswith',
                                         'endswith', 'iendswith', 'isnull']:
                    continue

                if filter_type == 'isnull':
                    if (isinstance(value, basestring) and value.upper == 'TRUE') or \
                       (isinstance(value, (int, bool)) and value):
                        value = True
                    else:
                        value = False

                if field_name in ["canonical_smiles", "standard_inchi", "standard_inchi_key"]:
                    field_name = ('compoundstructures' + LOOKUP_SEP) + field_name
                elif field_name in ["full_molformula",  "full_mwt"]:
                    field_name = ('compoundproperties' + LOOKUP_SEP) + field_name

                qs_filters = {}
                qs_filter = "%s%s%s" % (field_name, LOOKUP_SEP, filter_type)
                qs_filters[qs_filter] = value
                new_filter = Q(**dict_strip_unicode_keys(qs_filters))

                if not ret:
                    ret = new_filter
                else:
                    if logic.upper() == 'AND':
                        ret = ret & new_filter
                    else:
                        ret = ret | new_filter
                logic = filter.get('logic')
        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        qs_filters = {}

        if getattr(self._meta, 'queryset', None) is not None:
            # Get the possible query terms from the current QuerySet.
            query_terms = self._meta.queryset.query.query_terms
        else:
            query_terms = QUERY_TERMS

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if not field_name in self.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters)

#-----------------------------------------------------------------------------------------------------------------------

    def sdf_response_generator(self, objects):
        return (obj + '$$$$\n' for obj in objects.values_list('compoundstructures__molfile', flat=True))

#-----------------------------------------------------------------------------------------------------------------------

    def csv_response_generator(self, objects, request):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        for obj in objects:
            data = self.full_dehydrate(self.build_bundle(obj=obj, request=request), for_list=True).data
            molregno = data.get('molregno')
            chembl_id = data.get('chembl_id')
            pref_name = data.get('pref_name')
            canonical_smiles = data.get('structure').data.get('canonical_smiles')
            full_molformula = data.get('properties').data.get('full_molformula')
            inchi = data.get('structure').data.get('standard_inchi')
            standard_inchi_key = data.get('structure').data.get('canonical_smiles')
            full_mwt = data.get('properties').data.get('full_molformula')
            yield writer.writerow([molregno, chembl_id, pref_name, canonical_smiles, full_molformula, inchi,
                   standard_inchi_key, full_mwt])


#-----------------------------------------------------------------------------------------------------------------------

    def create_response(self, request, data, response_class=HttpResponse, **response_kwargs):
        """
        Extracts the common "which-format/serialize/return-response" cycle.

        Mostly a useful shortcut/hook.
        """
        desired_format = self.determine_format(request)
        if desired_format in ('chemical/x-mdl-sdfile', 'text/csv'):
            if desired_format == 'chemical/x-mdl-sdfile':
                streaming_content = self.sdf_response_generator(data)
                filename = "result.sdf"
            else:
                streaming_content = self.csv_response_generator(data, request)
                filename = "result.csv"
            response = StreamingHttpResponse(streaming_content=streaming_content,
                        content_type=build_content_type(desired_format), **response_kwargs)
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return response
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=build_content_type(desired_format), **response_kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if hasattr(request, 'format') and request.format in self._meta.serializer.formats:
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(ChemblBaseModelResource, self).determine_format(request)

#-----------------------------------------------------------------------------------------------------------------------

    def error_response(self, request, errors, response_class=None):
        """
        Extracts the common "which-format/serialize/return-error-response"
        cycle.

        Should be used as much as possible to return errors.
        """
        if response_class is None:
            response_class = http.HttpBadRequest

        desired_format = None

        if request:
            if request.GET.get('callback', None) is None:
                try:
                    desired_format = self.determine_format(request)
                except BadRequest:
                    pass  # Fall through to default handler below
            else:
                # JSONP can cause extra breakage.
                desired_format = 'application/json'

        if not desired_format or desired_format in ('chemical/x-mdl-sdfile', 'text/csv'):
            desired_format = self._meta.default_format

        try:
            serialized = self.serialize(request, errors, desired_format)
        except BadRequest as e:
            error = "Additional errors occurred, but serialization of those errors failed."

            if settings.DEBUG:
                error += " %s" % e

            return response_class(content=error, content_type='text/plain')

        return response_class(content=serialized, content_type=build_content_type(desired_format))

#-----------------------------------------------------------------------------------------------------------------------

    def dispatch(self, request_type, request, **kwargs):
        """
        Handles the common operations (allowed HTTP method, authentication,
        throttling, method lookup) surrounding most CRUD interactions.
        """
        allowed_methods = getattr(self._meta, "%s_allowed_methods" % request_type, None)

        if 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
            request.method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']

        request_method = self.method_check(request, allowed=allowed_methods)
        method = getattr(self, "%s_%s" % (request_method, request_type), None)

        if method is None:
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        self.is_authenticated(request)
        self.throttle_check(request)

        # All clear. Process the request.
        request = convert_post_to_put(request)
        response = method(request, **kwargs)

        # Add the throttled request.
        self.log_throttled_access(request)

        # If what comes back isn't a ``HttpResponse``, assume that the
        # request was accepted and that some action occurred. This also
        # prevents Django from freaking out.
        if not isinstance(response, HttpResponseBase):
            return http.HttpNoContent()

        return response

#-----------------------------------------------------------------------------------------------------------------------
