from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView


class UploadImage(APIView):
    def post(self, request):
        myfile = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return Response({
            'location': uploaded_file_url
        })