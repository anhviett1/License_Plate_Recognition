from django.urls import path
from . import views

urlpatterns = [
    path('', views.license_plate_list, name='license_plate_list'),
    path('add/', views.license_plate_add, name='add_license_plate'),
    path('edit/<int:id>/', views.license_plate_edit, name='edit_license_plate'),
    path('delete/<int:id>/', views.license_plate_delete, name='delete_license_plate'),
    path('upload/', views.upload_image, name='upload_image'),
    path('video_feed/', views.video_feed, name='video_feed'),
]



