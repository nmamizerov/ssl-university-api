from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status, serializers

class ProtectedSerializer(serializers.Serializer):
    class_name = serializers.SerializerMethodField()
    pk = serializers.CharField()

    def get_class_name(self, instance):
        return instance.__class__.__name__


def application_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if exc.__class__.__name__ == 'ProtectedError':
        return Response(ProtectedSerializer(exc.protected_objects, many=True).data, status=status.HTTP_409_CONFLICT)
    else:
        return response
