from django.urls import path
from .views import CompressImageView

urlpatterns = [
    path('compress-image/', CompressImageView.as_view(), name='compress-image'),
]
