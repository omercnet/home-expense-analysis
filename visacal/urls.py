__author__ = 'maord'

from django.urls import path

from . import tasks

urlpatterns = [
    path('refresh', tasks.refresh_all_users)
]
