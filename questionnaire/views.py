from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    return render(request, 'questionnaire/login.html')

def test(request):
    return render(request, 'questionnaire/test_start.html')

def test_generale(request):
    return render(request, 'questionnaire/test_generale.html')

def test_singola(request):
    return render(request, 'questionnaire/test_singola.html')

def test_checkbox(request):
    return render(request, 'questionnaire/test_checkbox.html')

def test_specifica(request):
    return render(request, 'questionnaire/test_specifica.html')

def result(request):
    return render(request, 'questionnaire/result.html')

def test_start(request):
    return render(request, 'questionnaire/test_start.html')
