from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns
    path('', views.index, name='index'),  # Home page URL
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    
    path('hostel/<int:hostel_id>/floors/', views.get_floors, name='get_floors'),
    path('get_room_details/', views.get_room_details, name='get_room_details'),
    path('book_room/', views.book_room, name='book_room'),
    path('rooms/',views.room_allocation,name='room_allocation'),
    path('profile/', views.profile, name='profile'),
    
]