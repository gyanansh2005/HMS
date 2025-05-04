from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('room_allocation/', views.room_allocation_page, name='das_room_allocation'),
    path('feedback/', views.submit_feedback_page, name='submit_feedback'),
    path('room_allocations/', views.room_allocations, name='room_allocations'),
    path('room_allocations/add/', views.add_room_allocation, name='add_room_allocation'),
    path('room_allocations/edit/<int:id>/', views.edit_room_allocation, name='edit_room_allocation'),
    path('room_allocations/delete/<int:id>/', views.delete_room_allocation, name='delete_room_allocation'),
    path('users/', views.users, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:id>/', views.delete_user, name='delete_user'),
    path('feedbacks/', views.feedbacks, name='feedbacks'),
    path('feedbacks/add/', views.add_feedback, name='add_feedback'),
    path('feedbacks/edit/<int:id>/', views.edit_feedback, name='edit_feedback'),
    path('feedbacks/delete/<int:id>/', views.delete_feedback, name='delete_feedback'),
    path('requests/', views.requests_list, name='requests_list'),
    path('requests/add/', views.add_request, name='add_request'),
    path('requests/edit/<int:id>/', views.edit_request, name='edit_request'),
    path('requests/delete/<int:id>/', views.delete_request, name='delete_request'),
    
    # API Routes
    path('api/users/', views.users, name='api_users'),
    path('api/users/<int:id>/', views.get_user, name='api_get_user'),
    path('api/users/edit/<int:id>/', views.edit_user, name='api_edit_user'),
    path('api/users/delete/<int:id>/', views.delete_user, name='api_delete_user'),
]