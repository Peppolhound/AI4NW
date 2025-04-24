from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    return render(request, 'questionnaire/login.html')

def test(request):
    return render(request, 'questionnaire/test_checkMultiple.html')

def test_testo(request):
    return render(request, 'questionnaire/test_testo.html')

def test_checkbox(request):
    return render(request, 'questionnaire/test_checkbox.html')

