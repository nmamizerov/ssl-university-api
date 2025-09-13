from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import TeachersSerializer
import boto3
from botocore.exceptions import ClientError
from .models import Teacher
class GetTeachers(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        teachers = Teacher.objects.all().order_by('-order')
        return Response(TeachersSerializer(
                teachers, many=True).data,
            200
            )
class GetTeacher(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        slug = request.GET.get('slug')
        teachers = Teacher.objects.filter(slug = slug).first()
        return Response(TeachersSerializer(
                teachers).data,
            200
            )
class ChooseTeacher(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data['name']
        contact = request.data['contact']
        teacher = request.data['teacher']     
        text = request.data['text']
        SENDER = "Simulator <teach@edu.skillslab.center>"     
        RECIPIENT = "yuri@klimenko.info"  
        SUBJECT = "Новая заявка"
        BODY_TEXT = ("Имя:"+ name +" контакт: "+contact+" Текст: "+text + " Преподаватель: "+ teacher
             )
        CHARSET = "UTF-8"
        client = boto3.client('ses',
                      region_name="us-east-2",
                      aws_access_key_id='AKIART7OG7KE7X6IMQ6A',
                      aws_secret_access_key='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')
        try:
        # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT, "alyona.serova.unium@gmail.com"
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        }
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
    # Display an error if something goes wrong.	
        except ClientError as e:

            return Response(e.response['Error']['Message'],
                    400
                    )
        else:
            return Response('OK',
                    200
                    )
# Create your views here.
