import requests

from django.db import models
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from emails.models import Email
from payments.models import Payment, PromoCode

from django.core.validators import FileExtensionValidator
from simulator_groups.models import SimulatorGroup
from django.db.models import Max

User = get_user_model()


class Simulator(models.Model):
    completed_by_user_set = models.ManyToManyField(User, blank=True, related_name='completed_simulators')
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField(default=30000)
    domain = models.CharField(max_length=200, unique=True)
    alias = models.CharField(max_length=255, unique=True, null=True, blank=True)
    color = models.CharField(max_length=255, default="#08a2dc")
    description = models.TextField()
    picture = models.ImageField(upload_to='simulator_images', blank=True, null=True)
    logo = models.ImageField(upload_to='simulator_logos', blank=True, null=True)
    favicon = models.ImageField(upload_to='simulator_favicons', blank=True, null=True)
    owner_generated_domain = models.CharField(max_length=200, unique=True, null=True, blank=True)
    admin_comment_request_price = models.PositiveIntegerField(default=10)
    group = models.ForeignKey(SimulatorGroup, on_delete=models.CASCADE)
    order_lesson = models.BooleanField(default=False)
    onboarding_skip = models.BooleanField(default=False, null=True, blank=True)
    onboarding_name = models.CharField(max_length=200, default='Онбординг', null=True, blank=True)
    simulator_script = models.TextField(null=True, blank=True)
    sequence_no = models.PositiveIntegerField(null=True)
    css = models.FileField(upload_to='simulator_css', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['css'])])
    token = models.CharField(max_length=32, blank=True, null=True, unique=True)
    notifications_url = models.CharField(max_length=300, blank=True, null=True)
    agreement_url = models.CharField(max_length=300, blank=True, null=True)
    data_processing_url = models.CharField(max_length=300, blank=True, null=True)

    welcome_message_text = models.TextField(null=True, blank=True)
    welcome_message_author_name = models.CharField(null=True, blank=True, max_length=255)
    welcome_message_author_img = models.ImageField(upload_to='simulator_images', blank=True, null=True)
    main_color = models.CharField(null=True, blank=True, max_length=255)
    message_after_task = models.TextField(null=True, blank=True)
    message_after_chapter = models.TextField(null=True, blank=True)
    text_button_after_chapter = models.CharField(null=True, blank=True, max_length=255)

    pay_terminal_key = models.CharField(null=True, blank=True, max_length=255)
    pay_password = models.CharField(null=True, blank=True, max_length=255)
    pay_email_company = models.CharField(null=True, blank=True, max_length=255)
    pay_type = models.CharField(max_length=255, default='tinkoff', choices=Payment.TYPE_CHOICES)
    pay_url = models.CharField(max_length=255, null=True, blank=True)
    vat = models.IntegerField(null=True, blank=True)

    telegram = models.CharField(null=True, blank=True, max_length=300)
    facebook = models.CharField(null=True, blank=True, max_length=300)
    vkontakte = models.CharField(null=True, blank=True, max_length=300)
    whatsapp = models.CharField(null=True, blank=True, max_length=300)

    recommended_volume = models.IntegerField(blank=True, null=True)

    theory_award = models.IntegerField(blank=True, default=0)
    message_award = models.IntegerField(blank=True, default=0)
    safetext_award = models.IntegerField(blank=True, default=0)
    test_award_correct = models.IntegerField(blank=True, default=0)
    test_award_error = models.IntegerField(blank=True, default=0)
    question_award_correct = models.IntegerField(blank=True, default=0)
    question_award_error = models.IntegerField(blank=True, default=0)
    questionuserchoice_award = models.IntegerField(blank=True, default=0)
    openquestion_award = models.IntegerField(blank=True, default=0)
    openquestionexpert_award = models.IntegerField(blank=True, default=0)
    questionanswercheck_award_correct = models.IntegerField(blank=True, default=0)
    questionanswercheck_award_error = models.IntegerField(blank=True, default=0)

    need_pause = models.BooleanField(blank=True, null=True)
    pause_length = models.IntegerField(blank=True, null=True)
    pause_text = models.TextField(blank=True, null=True)

    random_icon = models.TextField(blank=True, null=True)
    random_text = models.TextField(blank=True, null=True)
    random_link = models.CharField(max_length=2000, blank=True, null=True)
    random_showing = models.BooleanField(blank=True, null=True)
    show_page_mark = models.BooleanField(default=True)
    show_store = models.BooleanField(default=False)
    
    button_next_text = models.CharField(max_length=500, blank=True, null=True)
    button_theory_text = models.CharField(max_length=500, blank=True, null=True)
    button_notifications_text = models.CharField(max_length=500, blank=True, null=True)
    profile_text = models.CharField(max_length=500, blank=True, null=True)
    created_on_platform_text = models.CharField(max_length=500, blank=True, null=True)
    start_text = models.CharField(max_length=500, blank=True, null=True)
    continue_text = models.CharField(max_length=500, blank=True, null=True)
    soon_text = models.CharField(max_length=500, blank=True, null=True)
    need_complet_prev_chapters_text = models.CharField(max_length=500, blank=True, null=True)
    ended_text = models.CharField(max_length=500, blank=True, null=True)
    signin_text = models.CharField(max_length=500, blank=True, null=True)
    login_text = models.CharField(max_length=500, blank=True, null=True)
    why_comment_text = models.CharField(max_length=500, blank=True, null=True)
    will_answers_text = models.CharField(max_length=500, blank=True, null=True)
    will_author_answer_text = models.CharField(max_length=500, blank=True, null=True)
    pass_recover_text = models.CharField(max_length=500, blank=True, null=True)
    makeuser_text = models.TextField(null=True, blank=True)
    buy = models.CharField(max_length=255, null=True, blank=True)
    need_buy = models.CharField(max_length=255, null=True, blank=True)
    makeuser_title_text = models.CharField(max_length=255, null=True, blank=True)
    surname_text = models.CharField(max_length=255, null=True, blank=True)
    name_text = models.CharField(max_length=255, null=True, blank=True)
    gender_text = models.CharField(max_length=255, null=True, blank=True)
    done_text = models.CharField(max_length=255, null=True, blank=True)
    email_text = models.CharField(max_length=255, null=True, blank=True)
    placeholder_name_text = models.CharField(max_length=255, null=True, blank=True)
    placeholder_surname_text = models.CharField(max_length=255, null=True, blank=True)
    placeholder_email_text = models.CharField(max_length=255, null=True, blank=True)
    man_text = models.CharField(max_length=255, null=True, blank=True)
    woman_text = models.CharField(max_length=255, null=True, blank=True)
    man_small_text = models.CharField(max_length=255, null=True, blank=True)
    woman_small_text = models.CharField(max_length=255, null=True, blank=True)
    edit_user_title_text = models.CharField(max_length=255, null=True, blank=True)
    back_text = models.CharField(max_length=255, null=True, blank=True)
    edit_user_text = models.CharField(max_length=255, null=True, blank=True)
    auto_save_text = models.CharField(max_length=255, null=True, blank=True)
    logout_text = models.CharField(max_length=255, null=True, blank=True)
    fill_all_text = models.CharField(max_length=255, null=True, blank=True)
    required_text = models.CharField(max_length=255, null=True, blank=True)
    shop_text = models.CharField(max_length=255, null=True, blank=True)
    certificate_text = models.CharField(max_length=255, null=True, blank=True)
    password_text = models.CharField(max_length=255, null=True, blank=True)
    password_placeholder_text = models.CharField(max_length=255, null=True, blank=True)
    password_dont_match_text = models.CharField(max_length=255, null=True, blank=True)
    min_password_text = models.CharField(max_length=255, null=True, blank=True)
    repeat_password_text = models.CharField(max_length=255, null=True, blank=True)
    forget_pass_btn_text = models.CharField(max_length=255, null=True, blank=True)
    you_text = models.CharField(max_length=255, null=True, blank=True)
    bought_text = models.CharField(max_length=255, null=True, blank=True)
    price_text = models.CharField(max_length=255, null=True, blank=True)
    have_promo_text = models.CharField(max_length=255, null=True, blank=True)
    promocode_text = models.CharField(max_length=255, null=True, blank=True)
    author_comment_text = models.CharField(max_length=255, null=True, blank=True)
    send_text = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=255, null=True, blank=True)

    @property
    def onboarding_id(self):
        return self.onboarding.id
        
    @property
    def max_seq_no(self):
        seq_no = Simulator.objects.filter(group=self.group).aggregate(Max("sequence_no"))['sequence_no__max']
        if seq_no:
            seq_no = seq_no + 1
        else:
            seq_no = 1
        return seq_no

    def is_user_owner(self, user):
        return self.group.owner == user

    def create_onboarding(self):
        from pages.models import Page
        onboarding = Page(name="Онбоардинг", is_onboarding_for = self)
        onboarding.save()

    def complete(self, user):
        sim_user = SimulatorUser.objects.get(simulator=self, user=user)
        sim_user.simulator_completed = True
        sim_user.save()

    def configure_css(self, text):
        name = "simulator{}.css".format(self.id)
        self.css.save(name, ContentFile(text, name))

    def send_email(self, type, user, password=None):
        email = Email.objects.filter(simulator=self, email_type=type).first()
        if email:
            email.send_email(user=user, email_sender=self.group.email_sender, password=password)

    def __str__(self):
        return '({}) {}'.format(self.id, self.name)


class SimulatorUser(models.Model):
    simulator = models.ForeignKey(Simulator, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_page = models.ForeignKey('pages.Page', on_delete=models.SET_NULL, null=True, blank=True)
    onboarding_complete = models.BooleanField(default=False)
    simulator_paid = models.BooleanField(default=False)
    simulator_completed = models.BooleanField(default=False)
    first_uncompleted_lesson = models.ForeignKey('lessons.lesson', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, auto_now_add=True)

    def pay(self, **kwargs):
        promo_code = None
        price = self.simulator.price
        if 'promo_code' in kwargs:
            promo_code = get_object_or_404(PromoCode, slug=kwargs['promo_code'], simulator=self.simulator)
            price = promo_code.price

        payment = Payment.objects.create(
            sum=price,
            description=self.simulator.name if not promo_code else 'Promo code: {}'.format(promo_code.slug),
            simulator=self,
            return_url=self.simulator.alias if self.simulator.alias else self.simulator.domain,
            promo_code=promo_code,
            backend=self.simulator.pay_type
        )
        return payment.pay()

    def finish_payment(self, **kwargs):
        self.simulator_paid = True
        self.save()

        if self.simulator.notifications_url:
            data = {
                "user_id": self.user.id,
                "user_email": self.user.email,
                "simulator_id": self.simulator.id,
                "price": kwargs['sum'],
                "promo_code": kwargs['promo_code'] if kwargs['promo_code'] else ""
            }

            requests.post(self.simulator.notifications_url, data)

    def cancel_payment(self):
        self.simulator.send_email(2, self.user)

    def __str__(self):
        return '({}) {} - {}'.format(self.id, self.simulator.name, self.user.email)

