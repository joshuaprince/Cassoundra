from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.db import OperationalError
from django.views import generic
from django.db.models import Sum

from .forms import UploadFileForm

from cassupload import models


def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/upload/success')
    else:
        form = UploadFileForm()
    return render(request, 'cassupload/upload.html', {'form': form})


class CassListView(generic.ListView):
    template_name = 'cassupload/list.html'
    context_object_name = 'cass_sound_list'

    try:
        total_plays = models.Sound.objects.all().aggregate(Sum('play_count'))['play_count__sum']
    except OperationalError:  # The database is empty.
        total_plays = 0

    def get_queryset(self):
        return models.Sound.objects.order_by('-id')
