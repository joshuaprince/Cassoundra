from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'cassupl'
urlpatterns = [
    # /upload/
    url(r'^$', views.upload, name='upload'),
    # /upload/success/
    url(r'^success/$', TemplateView.as_view(template_name='cassupl/success.html'), name='success')
]
