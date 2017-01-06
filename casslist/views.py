from django.views import generic

from cassupload import models


class CassListView(generic.ListView):
    template_name = 'casslist/index.html'
    context_object_name = 'cass_sound_list'

    def get_queryset(self):
        return models.Sound.objects.order_by('-id')
