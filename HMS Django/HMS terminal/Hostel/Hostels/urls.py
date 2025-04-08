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
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),    
    path('hostel/<int:hostel_id>/floors/', views.get_floors, name='get_floors'),
    path('get_room_details/', views.get_room_details, name='get_room_details'),
    path('book_room/', views.book_room, name='book_room'),
    path('rooms/',views.room_allocation,name='room_allocation'),
    path('profile/', views.profile, name='profile'),
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('get_available_rooms/', views.get_available_rooms, name='get_available_rooms'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update_profile_pic/', views.update_profile_pic, name='update_profile_pic'),
    
    path('hosteldetails/', views.hostel_details, name='hostel_details'),    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)