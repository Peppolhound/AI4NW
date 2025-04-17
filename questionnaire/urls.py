from django.urls import path
from . import views

urlpatterns = [
    # Example URL patterns
    path('', views.home, name='home'),
    # path('about/', views.about, name='about'),
]