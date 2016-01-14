__author__ = 'mnowotka'

from tastypie import fields
from base64 import b64encode

#-----------------------------------------------------------------------------------------------------------------------

class BlobField(fields.ApiField):
    def convert(self, value):
        return b64encode(value)

#-----------------------------------------------------------------------------------------------------------------------
