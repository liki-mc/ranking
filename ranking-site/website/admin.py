from django.contrib import admin

from . import models

# Register your models here.
admin.site.register(models.Ranking)
admin.site.register(models.Entry)