from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='home'),
    path('room_allocation/',views.room_allocation,name='room_allocation'),
    path('complaint_and_maintenance/',views.complaint_and_maintenance,name='complaint_and_maintenance'),
    path('hostel_details/',views.hostel_details,name='hostel_details'),
    path('feedback/', views.feedback, name='feedback'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('payment/', views.payment, name='payment'),
]