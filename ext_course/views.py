from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .models import CourseReg, Course, CoursePromocode, AmoData
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from payments.models import Payment
from bot.views import send_ext_course_info
import json
import requests
import logging

# logging.basicConfig(filename='example.log', level=logging.DEBUG)
# Create your views here.


class SendToTG(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # logging.debug(123456)
        # logging.debug(request.data)
        send_ext_course_info(
            -1002070362305, json.dumps(request.data, ensure_ascii=False).encode("utf8")
        )
        return Response(status=200)


class CreateClient(APIView):
    permission_classes = [AllowAny]

    def post(self, request, id):
        course = Course.objects.filter(pk=id).first()
        price = course.price
        # провреть промокод
        if "promocode" in request.data:
            promo = CoursePromocode.objects.filter(
                Q(text=request.data["promocode"].lower().strip()) & Q(course=course)
            ).first()
            if promo is not None:
                price = promo.price
        # добавить новую заявку
        courseReg = CourseReg.objects.create(
            name=request.data["name"],
            email=request.data.get("email", None),
            phone=request.data.get("phone", None),
            additional=request.data.get("additional", None),
            course=course,
            promocode=request.data.get("promocode", None),
            final_price=price,
            to_amo=request.data.get("to_amo", True),
            utm_source=request.data.get("utm_source", ""),
            utm_medium=request.data.get("utm_medium", ""),
            utm_campaign=request.data.get("utm_campaign", ""),
            utm_content=request.data.get("utm_content", ""),
            utm_term=request.data.get("utm_term", ""),
        )

        courseReg.start(request.data.get("is_credit", False))
        # сделать платеж
        thisPayment = Payment.objects.create(
            ext_course=courseReg,
            sum=price,
            is_credit=request.data.get("is_credit", False),
            return_url="https://skillslab.center",
        )
        response = None
        if request.data.get("is_credit"):
            response = requests.post(
                "https://api.payments.skillslab.center/api/v1/payments/credit/init/",
                json={
                    "amount": price,
                    "user_email": request.data["email"],
                    "description": thisPayment.product.name,
                    "data": {"name": thisPayment.product.name},
                },
            )
        else:
            response = requests.post(
                "https://api.payments.skillslab.center/api/v1/payments/init/",
                json={
                    "amount": price,
                    "user_email": request.data["email"],
                    "description": thisPayment.product.name,
                    "data": {"name": thisPayment.product.name},
                },
            )

        if response.status_code != 200:
            return Response(status=400)
        answer = response.json()
        thisPayment.payment_id = answer["id"]
        thisPayment.save()
        return Response(answer, status=status.HTTP_200_OK)


class PaymentNotificaiton(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payment = Payment.objects.filter(payment_id=request.data["id"]).first()
        print(payment)
        print(request.data["id"])
        if not payment:
            return Response(status=404)
        status = request.data["status"]
        if status in (
            "REJECTED",
            "REFUNDED",
            "CANCELED",
            "Fail",
            "AUTH_FAIL",
            "canceled",
        ):
            payment.status = 0
            payment.save()
            if payment.ext_course is not None:
                payment.ext_course.unsuccess_payment()
        elif (
            status
            in (
                "CONFIRMED",
                "Authorized",
                "AUTHORIZED",
                "Completed",
                "COMPLETED",
                "signed",
            )
            and payment.status != 2
        ):
            payment.status = 2
            payment.save()
            if payment.ext_course is not None:
                payment.ext_course.success_payment()
        payment.status = request.data["status"]

        payment.save()
        return Response(status=200)
