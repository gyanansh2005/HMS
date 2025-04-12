from django.contrib import admin
from app2.models import Form

# Register your models here.
admin.site.register(Form)

from django.contrib import admin
from .models import MessMenu

admin.site.register(MessMenu)