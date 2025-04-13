from django.urls import path
from . import views

urlpatterns = [
    path('', views.app2index, name='app2index'),
    path('admin_form/', views.admin_form, name='admin_form'),
    path('events/', views.events, name='events'),
    path('base/', views.base, name='base'),
    path('delete-event/<int:id>/', views.delete, name='delete'),
    path('update-event/<int:id>/', views.update, name='update'),
    path('mess/', views.mess, name='mess'),
    path('discussion/', views.discussion_center, name='discussion_center'),
    path('lost-and-found/', views.lost_and_found_dashboard, name='lost_and_found_dashboard'),
    path('claim/<int:item_id>/', views.claim_item, name='claim_item'),
    path('claims/manage/', views.manage_claims, name='manage_claims'),
    path('claims/approve/<int:claim_id>/', views.approve_claim, name='approve_claim'),
    path('mess/set-today/<int:menu_id>/', views.set_today_menu, name='set_today_menu'),
    path('mess/update/<int:menu_id>/', views.update_mess_menu, name='update_mess_menu'),
    path('mess/delete/<int:menu_id>/', views.delete_mess_menu, name='delete_mess_menu'),
    path('discussion/delete-notification/<int:msg_id>/', views.delete_notification, name='delete_notification'),
]