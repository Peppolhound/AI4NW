from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),

    path('test/', views.test, name='test'),
    path('test_generale/', views.test_generale, name='test_generale'),
    path('test_singola/', views.test_singola, name='test_singola'),           
    path('test_checkbox/', views.test_checkbox, name='test_checkbox'),
    path('test_specifica/', views.test_specifica, name='test_specifica'),  
    path('next-question/', views.nextQuestion, name='next_question'),
    # path('previous-question/<int:questionId>/', views.prevQuestion, name='previous_question'),
    path('result/', views.result, name='result'),  
]