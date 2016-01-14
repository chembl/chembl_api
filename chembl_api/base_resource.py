__author__ = 'mnowotka'

from django.conf.urls import *
from django.core.paginator import InvalidPage
from django.utils import six
from django.http import Http404
from tastypie.resources import ModelResource
from tastypie.resources import ModelDeclarativeMetaclass
from tastypie.paginator import Paginator
from haystack.query import SearchQuerySet
from tastypie.utils import trailing_slash

# If ``csrf_exempt`` isn't present, stub it.
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(func):
        return func


#-----------------------------------------------------------------------------------------------------------------------

class ChemblBaseModelResource(six.with_metaclass(ModelDeclarativeMetaclass, ModelResource)):

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/search\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>[\w\s/-][\w\s/;-]*)/$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>[\w\s/-]*)%s$" % (self._meta.resource_name, self.defaultIndex, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<%s>[\w\s/-]*)\.(?P<format>\w+)%s$" % (self._meta.resource_name, self.defaultIndex, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if (hasattr(request, 'format') and
            request.format in self._meta.serializer.formats):
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(ChemblBaseModelResource, self).determine_format(request)

#-----------------------------------------------------------------------------------------------------------------------

    #This is made only for maintaining backwards compatibility with old spring based chembl api and should be removed
    def dispatch_list(self, request, **kwargs):
        k = kwargs.pop('k', None)
        v = kwargs.pop('v', None)
        if (k,v) != (None, None):
            get = request.GET.copy()
            get[k] = v
            request.GET = get
        return super(ChemblBaseModelResource, self).dispatch_list(request, **kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.pop('format', None)
            wrapped_view = super(ChemblBaseModelResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)
        return wrapper

#-----------------------------------------------------------------------------------------------------------------------

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(ChemblBaseModelResource, self).build_filters(filters)

        if "q" in filters:
            sqs = SearchQuerySet().auto_query(filters['q'])

            orm_filters["pk__in"] = [i.pk for i in sqs]

        return orm_filters

#-----------------------------------------------------------------------------------------------------------------------

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Do the query.
        ret = []
        for field in self._meta.object_class.haystack_index:
            kwargs = {field: request.GET.get('q', '')}
            sqs = SearchQuerySet().models(self._meta.object_class).autocomplete(**kwargs)
            ret.extend(sqs)
        paginator = Paginator(request.GET, ret)

        try:
            page = paginator.page()
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page['objects']:
            bundle = self.build_bundle(obj=result.object, request=request)
            bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

#-----------------------------------------------------------------------------------------------------------------------
