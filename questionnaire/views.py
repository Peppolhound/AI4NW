from django.shortcuts import render
from .utils import *
from .models import Questionnaire
from django.core.serializers import serialize
import json

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
                    questionnaire = parseJSON(questionnaireJSON)
                    first_group = Group.objects.filter(questionnaireId=questionnaire.questionnaireId).order_by('order').first() # SELEZIONO IL PRIMO GRUPPO con ID del questionario (in genere ANAMNESI)
                    questions = Question.objects.filter(groupId=first_group.groupId).order_by('order')              # SELEZIONO LE DOMANDE del primo gruppo
                    print(f"Questions: {questions}")
                    context_questions = {}
                    for question in questions:
                        q = {}
                        answers = Answer.objects.filter(questionId=question.questionId).order_by('order')  # SELEZIONO LE RISPOSTE per ogni domanda
                        q['questionId'] = question.questionId
                        q['description'] = question.description
                        q['typeQuestion'] = question.typeQuestion_description
                        q['groupId'] = question.groupId
                        q['order'] = question.order
                        answ = []
                        for answer in answers:
                            a = {}
                            a['answerId'] = answer.answerId
                            a['description'] = answer.description
                            a['order'] = answer.order
                            a['questionId'] = answer.questionId
                            answ.append(a)
                        q['answers'] = answ
                        if 'Sesso' in question.description: 
                            context_questions['sesso'] = q
                        elif 'Età' in question.description:
                            context_questions['eta'] = q
                        elif 'Altezza' in question.description:
                            context_questions['altezza'] = q
                        elif 'Peso' in question.description:
                            context_questions['peso'] = q
                        elif 'Fumo' in question.description:
                            context_questions['fumo'] = q
                        elif 'Addominale' in question.description:
                            context_questions['addominale'] = q

                # User login failed, show an error message
                context_questions['questionnaireId'] = questionnaire.questionnaireId
                context_questions['userId'] = userId
                # print(f"Context Questions: {context_questions['fumo']}")
        return render(request, 'questionnaire/test_generale.html', context=context_questions)
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
