from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('admin_form/',views.admin_form,name='admin_form'),
    path('events/', views.events, name='events'),
]