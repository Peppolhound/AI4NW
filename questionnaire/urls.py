from django.urls import path
from . import views

urlpatterns = [
    # Example URL patterns
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),
    path('login/', views.login, name='login'),
    # path('about/', views.about, name='about'),
]