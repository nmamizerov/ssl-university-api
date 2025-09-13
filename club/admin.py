from django.contrib import admin
from .models import Club, Game, Player, Tournament
from django.contrib.auth import get_user_model
from subscriptions.models import UserSubscription
from django.db.models import Q
User = get_user_model()

class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    autocomplete_fields = ('player1','player2')
    def render_change_form(self, request, context, *args, **kwargs):
        subs = UserSubscription.objects.filter(Q(type__gte = 5)&Q(subscription__is_club = True)).values_list('user__id', flat=True)
        context['adminform'].form.fields['player1'].queryset = User.objects.filter(pk__in = subs).order_by('last_name')
        context['adminform'].form.fields['player2'].queryset = User.objects.filter(pk__in = subs).order_by('last_name')
        return super(GameAdmin, self).render_change_form(request, context, *args, **kwargs)

class TournamentAdmin(admin.ModelAdmin):
    # readonly_fields = ('place1','place2', 'place3')
    autocomplete_fields = ('place1','place2', 'place3')

# Register your models here.
admin.site.register(Club)
admin.site.register(Player)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Game, GameAdmin)
