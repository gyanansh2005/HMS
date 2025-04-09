from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.app2index,name='app2index'),
    path('admin_form/',views.admin_form,name='admin_form'),
    path('events/', views.events, name='events'),
    path('base/', views.base, name='base'),
    path('update/', views.update, name='update'),
    path('delete-event/<int:id>/', views.delete, name='delete'),
    path('update-event/<int:id>/', views.update, name='update'),

]