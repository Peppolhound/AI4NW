from django.shortcuts import render
from .utils import *
from .models import Questionnaire

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    if request.method == 'POST':
        nome = request.POST.get('first_name')
        cognome = request.POST.get('last_name')
        birthdate = request.POST.get('birth_date')
        # print(f"Nome: {nome}, Cognome: {cognome}, Data di Nascita: {birthdate}")
        usercode = getUserCode(nome, cognome, birthdate)
        # print(f"Usercode: {usercode}")
        tokenId = loginApplicativo()
        if tokenId is not None:
            ################## DEBUG ##################
            # usercode = '9876'                       
            ################## DEBUG ##################
            userId = loginUtente(usercode, tokenId)
            print(f"UserId: {userId}")
            if userId is not None:
                # User login successful, redirect to the questionnaire page
                questionnaireJSON = getQuestionnaire(tokenId)
                # print(f"Questionnaire JSON: {questionnaireJSON}")
                if questionnaireJSON is not None:
                    # Save the questionnaire data to the database
                    questionnaireId = questionnaireJSON['questionnaireId']
                    if not Questionnaire.objects.filter(questionnaireId=questionnaireId).exists():
                        # Create a new Questionnaire object if it doesn't exist
                        q = parseJSON(questionnaireJSON)
                    else:
                        q = Questionnaire.objects.get(questionnaireId=questionnaireId)
                    # Render the questionnaire page with the userId
                    
                    # currentQuestion, answers = getFirstQuestion(q.questionnaireId)
                    # if currentQuestion is not None:
                    #     # Render the questionnaire page with the current question and answers
                    #     context = {
                    #         'questionnaireId': q.questionnaireId,
                    #         'userId': userId,
                    #         'question': currentQuestion,
                    #         'answers': answers
                    #     }
                    #     if currentQuestion.typeQuestion_description == 'checkbox':
                    #         return render(request, 'questionnaire/test_checkbox.html', context=context)
                    #     elif currentQuestion.typeQuestion_description == 'singola':
                    #         return render(request, 'questionnaire/test_singola.html', context=context)
                    #     elif currentQuestion.typeQuestion_description == 'specifica':
                    #         return render(request, 'questionnaire/test_specifica.html', context=context)
                        
                        # return render(request, 'questionnaire/questionnaire.html', context=context)
                    # else:
                    #     # Handle case where there are no questions available
                    #     return render(request, 'questionnaire/login.html', {'userId': userId})
                    # Handle case where questionnaire data is not available
                # User login failed, show an error message
        context = {
            'questionnaireId': questionnaireId,
            'userId': userId,
        }
        return render(request, 'questionnaire/test_generale.html', context=context)
    else:
        # If it's a GET request, just render the login page
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
