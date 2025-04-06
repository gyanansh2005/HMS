from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Room management
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('get_available_rooms/', views.get_available_rooms, name='get_available_rooms'),
    
    # User profile
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Payment
    path('payment/', views.payment, name='payment'),
    
    # Other features
    path('complaint_and_maintenance/', views.complaint_and_maintenance, name='complaint_and_maintenance'),
    path('feedback/', views.feedback, name='feedback'),
    path('hostel_details/', views.hostel_details, name='hostel_details'),
    path('about/', views.about, name='about'),
]