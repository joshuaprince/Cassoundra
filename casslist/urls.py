from django.conf.urls import url

from . import views

app_name = 'casslist'
urlpatterns = [
    # /list/
    url(r'^$', views.CassListView.as_view(), name='list'),
]
