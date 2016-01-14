__author__ = 'mnowotka'

import chembl_api.api as Api
from chembl_core_db.testing.tastypieTest import ResourceTestCase, TestApiClient
from django.template import TemplateDoesNotExist
from tastypie.serializers import Serializer

#-----------------------------------------------------------------------------------------------------------------------

class EntryResourceTest(ResourceTestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    fixtures = ['test_entries.json']

#-----------------------------------------------------------------------------------------------------------------------

    def setUp(self):
        super(EntryResourceTest, self).setUp()
        self.serializer = Serializer()
        self.api_client = TestApiClient(self.serializer)
        self.apiPath = "/api/" + Api.api.api_name

#-----------------------------------------------------------------------------------------------------------------------

    def test_get_list_json(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            if 'get' in resource._meta.list_allowed_methods:
                url = self.apiPath + '/' + name + '/'
                resp = self.api_client.get(url, format='json')
                self.assertValidJSONResponse(resp, url)

#-----------------------------------------------------------------------------------------------------------------------

    def test_get_schema_json(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            if 'get' in resource._meta.list_allowed_methods:
                url = self.apiPath + '/' + name + '/schema'
                resp = self.api_client.get(url, format='json')
                self.assertValidJSONResponse(resp, url)

#-----------------------------------------------------------------------------------------------------------------------

    def test_get_detail_json(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            count = resource._meta.object_class.objects.count()
            first_pk = None

            if count > 1:
                first_pk = str(resource._meta.object_class.objects.all()[0].pk)
            if 'get' in resource._meta.list_allowed_methods and first_pk:
                url = self.apiPath + '/' + name + '/' + first_pk
                try:
                    resp = self.api_client.get(url, format='json')
                except TemplateDoesNotExist as err:
                    raise Exception(url + " " + err.message)
                self.assertValidJSONResponse(resp, url)

#-----------------------------------------------------------------------------------------------------------------------

    def test_get_set_json(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            count = resource._meta.object_class.objects.count()
            first_pk = None
            second_pk = None

            if count > 1:
                first_pk = str(resource._meta.object_class.objects.all()[0].pk)

                if count == 2:
                    second_pk = str(resource._meta.object_class.objects.all()[1].pk)
                else:
                    second_pk = str(resource._meta.object_class.objects.all()[2].pk)

            if 'get' in resource._meta.list_allowed_methods and second_pk:
                url = self.apiPath + '/' + name + '/set/' + first_pk + ";" + second_pk + "/"
                try:
                    resp = self.api_client.get(url, format='json')
                except TemplateDoesNotExist as err:
                    raise Exception(url + " " + err.message)
                self.assertValidJSONResponse(resp, url)

#-----------------------------------------------------------------------------------------------------------------------

    def test_post(self):
        self.assertHttpCreated(self.api_client.post(self.apiPath + '/' + 'moleculedictionary' + '/', format='json', data={"structure_type": "MOL"}, content_type='json')) # TODO: post_data has to be something meaningful...


#-----------------------------------------------------------------------------------------------------------------------

    def test_put_detail(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            count = resource._meta.object_class.objects.count()
            first_pk = None

            if count > 1:
                first_pk = str(resource._meta.object_class.objects.all()[0].pk)

            if 'put' in resource._meta.list_allowed_methods and first_pk and False:
                self.assertHttpAccepted(self.api_client.put(self.apiPath + '/' + name + '/'  + first_pk, format='json', data=self.new_data)) # TODO: new_data has to be something meaningful...

#-----------------------------------------------------------------------------------------------------------------------

    def test_delete_detail(self):
        for item in Api.api._registry.items():
            name = item[0]
            resource = item[1]
            count = resource._meta.object_class.objects.count()
            first_pk = None

            if count > 1:
                first_pk = str(resource._meta.object_class.objects.all()[0].pk)
            if 'delete' in resource._meta.list_allowed_methods and first_pk and False:
                self.assertHttpAccepted(self.api_client.delete(self.apiPath + '/' + name + '/' + first_pk, format='json'))
                self.assertEqual(resource._meta.object_class.objects.count(), count - 1)

#-----------------------------------------------------------------------------------------------------------------------