from django.contrib import admin

from .models import CalUser, CalCard, CalExpense

admin.site.register(CalUser)
admin.site.register(CalCard)
admin.site.register(CalExpense)
