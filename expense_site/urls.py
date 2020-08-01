from django.urls import path
# from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include


urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('visacal/', include('visacal.urls')),
]
