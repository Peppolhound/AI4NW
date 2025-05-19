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
        # nome = request.POST.get('first_name')
        # cognome = request.POST.get('last_name')
        # birthdate = request.POST.get('birth_date')
        username = request.POST.get('login-info')
        # print(f"Nome: {nome}, Cognome: {cognome}, Data di Nascita: {birthdate}")
        usercode = getUserCode(username)
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
                            context_questions['questionId'] = q['questionId'] 
                        elif 'Età' in question.description:
                            context_questions['eta'] = q
                            context_questions['questionId'] = q['questionId'] 
                        elif 'Altezza' in question.description:
                            context_questions['altezza'] = q
                            context_questions['questionId'] = q['questionId'] 
                        elif 'Peso' in question.description:
                            context_questions['peso'] = q
                            context_questions['questionId'] = q['questionId'] 
                        elif 'Fumo' in question.description:
                            context_questions['fumo'] = q
                            context_questions['questionId'] = q['questionId'] 
                        elif 'Addominale' in question.description:
                            context_questions['addominale'] = q
                            context_questions['questionId'] = q['questionId'] 
                        

                # User login failed, show an error message
                context_questions['questionnaireId'] = questionnaire.questionnaireId
                context_questions['userId'] = userId
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


def nextQuestion(request, questionId):
    if request.method == 'POST':
        nextQuestionObj, nextAnswer, nextDescription = getNextQuestion(questionId)

        context_questions = {}
        if nextQuestionObj is None:
            context_questions['is_last_question'] = True
            return render(request, 'questionnaire/result.html')  # o una pagina di fine

        # Costruzione della domanda
        question = nextQuestionObj
        q = {
            'questionId': question.questionId,
            'description': question.description,
            'typeQuestion_description': question.typeQuestion_description,
            'typeQuestion_id': question.typeQuestion_idTypeQuestion,
            'groupId': question.groupId,
            'order': question.order
        }

        # Costruzione delle risposte
        answ = []
        for answer in nextAnswer:
            answ.append({
                'answerId': answer.answerId,
                'description': answer.description,
                'order': answer.order
            })

        q['answers'] = answ
        context_questions['q'] = q
        context_questions['questionId'] = q['questionId']
        context_questions['is_last_question'] = getNextQuestion(q['questionId'])[0] is None  # Verifica se ci sono ancora domande


        if nextDescription is not None:
            questionId = request.POST.get('questionId')
            if q['typeQuestion_id'] == "1":
                return render (request, 'questionnaire/test_checkbox.html', context=context_questions)
            if q['typeQuestion_id'] == "2":
                return render (request, 'questionnaire/test_specifica.html', context=context_questions)
            if q['typeQuestion_id'] == "3":
                return render (request, 'questionnaire/test_singola.html', context=context_questions)
            if q['typeQuestion_id'] == "4": #MEDIA - DA DEFINIRE
                return render (request, 'questionnaire/test_checkbox.html', context=context_questions)

        else:
            return render(request, 'questionnaire/result.html')

