from django.db import OperationalError
from django.views import generic
from django.db.models import Sum

from cassupload import models


class CassListView(generic.ListView):
    template_name = 'casslist/index.html'
    context_object_name = 'cass_sound_list'

    try:
        total_plays = models.Sound.objects.all().aggregate(Sum('play_count'))['play_count__sum']
    except OperationalError:  # The database is empty.
        total_plays = 0

    def get_queryset(self):
        return models.Sound.objects.order_by('-id')
