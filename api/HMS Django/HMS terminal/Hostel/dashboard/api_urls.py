from django.urls import path
from . import api_views

urlpatterns = [
    path('room_allocations/', api_views.room_allocation_list, name='api_room_allocations'),
    path('users/', api_views.user_list, name='api_users'),
    path('feedbacks/', api_views.feedback_list, name='api_feedbacks'),
    path('requests/', api_views.request_list, name='api_requests'),
]
