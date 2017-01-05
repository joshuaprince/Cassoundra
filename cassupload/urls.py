from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'cassupload'
urlpatterns = [
    # /upload/
    url(r'^$', views.upload, name='upload'),
    # /upload/success/
    url(r'^success/$', TemplateView.as_view(template_name='cassupload/success.html'), name='success')
]
