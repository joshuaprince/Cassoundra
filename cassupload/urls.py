from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'cassupload'
urlpatterns = [
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^upload/success/$', TemplateView.as_view(template_name='cassupload/success.html'), name='success'),
    url(r'^list/$', views.CassListView.as_view(), name='list')
]
