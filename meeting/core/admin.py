from django.contrib import admin

from .models import Participant, Schedules
# Register your models here.

admin.site.register(Participant)
admin.site.register(Schedules)