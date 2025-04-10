from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.app2index,name='app2index'),
    path('admin_form/',views.admin_form,name='admin_form'),
    path('events/', views.events, name='events'),
    path('base/', views.base, name='base'),
    path('update/', views.update, name='update'),
    path('mess/', views.mess, name='mess'),
    path('mess_admin/', views.mess_admin, name='mess_admin'),
    path('delete-event/<int:id>/', views.delete, name='delete'),
    path('update-event/<int:id>/', views.update, name='update'),
    path('mess_menu/update/<int:id>/', views.update_mess_menu, name='update_mess_menu'),
    path('mess_menu/delete/<int:id>/', views.delete_mess_menu, name='delete_mess_menu'),
    path('mess_menu/set_today/<int:id>/', views.set_today_menu, name='set_today_menu'),



]