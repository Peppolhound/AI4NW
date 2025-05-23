from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('test/', views.test, name='test'),
    path('test_intro/', views.test_intro, name='test_intro'),
    # path('test_singola/', views.test_singola, name='test_singola'),           
    # path('test_radio/', views.test_radio, name='test_radio'),
    # path('test_specifica/', views.test_specifica, name='test_specifica'),  
    path('next-question/', views.nextQuestion, name='next_question'),
    path('result/', views.result, name='result'),  


]