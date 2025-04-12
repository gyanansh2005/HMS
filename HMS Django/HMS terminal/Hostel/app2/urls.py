from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.app2index,name='app2index'),
    path('admin_form/',views.admin_form,name='admin_form'),
    path('events/', views.events, name='events'),
    path('base/', views.base, name='base'),
    path('update/', views.update, name='update'),

    path('delete-event/<int:id>/', views.delete, name='delete'),
    path('update-event/<int:id>/', views.update, name='update'),
    path('mess/', views.mess, name='mess'),
    path('discussion/', views.discussion_center, name='discussion_center'),

    path('lost_home/', views.home, name='home'),
    path('lost/report/', views.report_lost_item, name='report_lost'),
    path('found/report/', views.report_found_item, name='report_found'),
    path('lost/', views.lost_items, name='lost_items'),
    path('found/', views.found_items, name='found_items'),
    path('claim/<int:item_id>/', views.claim_item, name='claim_item'),
    path('claims/manage/', views.manage_claims, name='manage_claims'),
    path('claims/approve/<int:claim_id>/', views.approve_claim, name='approve_claim'),


]