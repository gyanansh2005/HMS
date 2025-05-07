from django.urls import path
from dashboard import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users, name='users'),
    path('users/<int:id>/', views.user_detail, name='user_detail'),
    path('complaints/', views.complaints, name='complaints'),
    path('feedback/', views.feedback, name='feedback'),
    path('allocations/', views.allocations, name='allocations'),
    path('delete_user/<int:id>/', views.delete_user, name='delete_user'),
    path('delete_complaint/<int:id>/', views.delete_complaint, name='delete_complaint'),
    path('delete_feedback/<int:id>/', views.delete_feedback, name='delete_feedback'),
    path('delete_allocation/<int:id>/', views.delete_allocation, name='delete_allocation'),
]