from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def test(request):
    return render(request, 'questionnaire/test.html')

def login(request):
    return render(request, 'questionnaire/login.html')