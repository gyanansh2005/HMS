
# Register your models here.
# rooms/admin.py
from django.contrib import admin
from .models import Hostel, Room, Student, Allocation

admin.site.register(Hostel)
admin.site.register(Room)
admin.site.register(Student)
admin.site.register(Allocation)