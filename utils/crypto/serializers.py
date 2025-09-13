from rest_framework import serializers
from ._cipher import cipher

ENCRYPTED_PREFIX = 'U2FsdGVk'  # base64.b64encode(b'Salted').decode()


class EncryptedField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            return self.fail('invalid')
        if data.startswith(ENCRYPTED_PREFIX):
            return data
        return cipher.b64encrypt(data)

    def to_representation(self, value):
        if not value:
            return None
        return str(value)