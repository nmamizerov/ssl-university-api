import logging

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from backend.application_viewset import AdminApplicationViewSet, ApplicationViewSet
from simulators.models import Simulator, SimulatorUser
from .models import PromoCode, Payment
from .serializers import PromoCodeSerializer, PaymentSerializer
from .permissions import PromoCodePermissions
from django.http import HttpResponse

logger = logging.getLogger("django.server")


class AdminPromoCodeViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = PromoCodeSerializer
    permission_classes = [PromoCodePermissions]

    def get_queryset(self):
        if "simulator" in self.params:
            queryset = PromoCode.objects.filter(simulator__id=self.params.get('simulator'))
        else:
            queryset = PromoCode.objects.all()
        return queryset


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    template_name = 'cloud_payment.html'

    @action(detail=False, methods=['post'], url_path='activate')
    def activate(self, request):
        if request.user.is_anonymous:
            return Response({"details": "Учетные данные не предоставлены"}, status=status.HTTP_401_UNAUTHORIZED)

        slug = request.data['promo_code']
        promo_code = get_object_or_404(PromoCode, slug=slug, simulator=request.simulator)

        success = promo_code.activate(request.user)
        return Response({
            'success': success,
            'price': promo_code.price,
            'promo_code': slug
        })

    @action(detail=True, methods=['get'], renderer_classes=[TemplateHTMLRenderer], url_path='pay_cloudpayments')
    def pay_cloudpayments(self, request, *args, **kwargs):
        payment = self.get_object()
        return Response({
            'publicId': payment.credentials.pay_TerminalKey,
            'name': payment.description,
            'amount': payment.sum,
            'accountId': payment.user.email,
            'invoiceId': payment.id,
            'vat': payment.vat,
        })

    @action(detail=False, methods=['post'], url_path='complete_cloudpayments')
    def complete_cloudpayments(self, request):
        context = request.data
        payment = Payment.objects.get(pk=int(context['InvoiceId']))

        if 'Status' not in context:
            context['Status'] = 'Fail'

        payment.check_bank_transaction_status(status=context['Status'])
        return Response({'code': 0})

    @action(detail=False, methods=['post'], url_path='complete_tinkoff')
    def complete_tinkoff(self, request):
        payment = Payment.objects.get(payment_id=int(request.data['PaymentId']))

        # переписываем, если платежка внешний курс
        if payment.ext_course is not None:
            status_t = request.data['Status']
            if status_t in ('REJECTED', 'REFUNDED','CANCELED',  'Fail', 'AUTH_FAIL'):
                payment.status = 0
                payment.save()
                payment.ext_course.unsuccess_payment()
            elif status_t in ('CONFIRMED', 'Authorized', 'AUTHORIZED', 'Completed', 'COMPLETED'):
                payment.status = 2
                payment.save()
                payment.ext_course.success_payment()
            return HttpResponse("OK", status=status.HTTP_200_OK)

        rebill_ID = None
        if payment.is_recurrent and 'RebillId' in request.data:
            rebill_ID = request.data['RebillId']

        payment.check_bank_transaction_status(status=request.data['Status'], rebill_ID=rebill_ID)
        return HttpResponse("OK", status=status.HTTP_200_OK)
