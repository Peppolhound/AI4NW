from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),

    path('test/', views.test, name='test'),
    path('test_testo/', views.test_testo, name='test_testo'),           
    path('test_checkbox/', views.test_checkbox, name='test_checkbox'), 
]