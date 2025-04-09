from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Other URL patterns
    path('', views.index, name='index'),  # Home page URL
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/',views.logout_view, name='logout'),    
    path('hostel/<int:hostel_id>/floors/', views.get_floors, name='get_floors'),
    path('get_room_details/', views.get_room_details, name='get_room_details'),
    path('book_room/', views.book_room, name='book_room'),
    path('rooms/',views.room_allocation,name='room_allocation'),
    path('profiles/', views.profiles, name='profiles'),
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('get_available_rooms/', views.get_available_rooms, name='get_available_rooms'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update_profile_pic/', views.update_profile_pic, name='update_profile_pic'),
    
    
    path('payment/', views.payment_page, name='payment'),
    path('payment/success/<str:transaction_id>/', views.payment_success, name='payment_success'),
    path('post-allocation/', views.post_allocation, name='post_allocation'),
    

    path('complaint/', views.complaint_maintenance, name='complaint_maintenance'),
    path('feedback/', views.feedback, name='feedback'),
    path('terms/', views.terms_conditions, name='terms_conditions'),
    
    
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/', views.dashboard, name='admin_dashboard'),  # For admin dashboard
    path('about/', views.about, name='about'),
    # Add these if not already present:
    path('profile/', views.profiles, name='profile'),
    # Add admin-specific views if not implemented yet
    path('requests/', views.view_requests, name='view_requests'),
    path('allocations/', views.view_allocations, name='view_allocations'),
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    
    path('staff_signup/', views.staff_signup_view, name='staff_signup'),
    

    
    path('hosteldetails/', views.hostel_details, name='hostel_details'),    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)