
from django.urls import path
from .views import list_video, merge_video, clean_storage

urlpatterns = [
    path('', list_video, name='list_video'),
    path('merge', merge_video, name='merge_download'),
    path('clean', clean_storage, name='clean_storage'),
]
