from django.shortcuts import render, redirect
from django.conf import settings
from .utils import *
from .models import Questionnaire, Group, Question, Answer, QuestionnaireValue, AnsweredQuestions
from django.core.files.storage import FileSystemStorage
from django.core.serializers import serialize
import datetime
import os
import json

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    questionnaireId = Questionnaire.objects.first().questionnaireId
    print(f"questionnaireId: {questionnaireId}") # stampa il valore di questionnaireId)
    return render(request, 'questionnaire/login.html', {'questionnaireId': questionnaireId})


def test(request):
    return render(request, 'questionnaire/test_start.html')

def test_generale(request):
    if request.method == 'POST':
        username = request.POST.get('login-info')
        usercode = getUserCode(username)
        tokenId = loginApplicativo()
        if tokenId is not None:
            ################## DEBUG ##################
            # usercode = '9876'                       
            ################## DEBUG ##################
            questionnaireId = request.POST.get('questionnaireId')
            QuestionnaireValue.objects.create(
                user_id=usercode,
                questionnaireId=questionnaireId
            )
            user_id= loginUtente(usercode, tokenId)
            context_questions = showGeneralitaForm(user_id)
            return render(request, 'questionnaire/test_generale.html', context=context_questions)
    else:
        # If it's a GET request, just render the login page
        return redirect('login')
    
def test_singola(request):
    return render(request, 'questionnaire/test_singola.html')

def test_checkbox(request):
    return render(request, 'questionnaire/test_checkbox.html')

def test_specifica(request):
    return render(request, 'questionnaire/test_specifica.html')

def result(request):
    today_date = datetime.date.today()
    if request.method == 'POST':
        question_keys = [k for k in request.POST.keys() if k.startswith("question_")]
        question_id = request.POST.get('questionId')
        custom_answer = request.POST.get(f'customAnswer_{question_id}', None)
        user_id = request.POST.get('userId')    
        

        if question_keys:
            question_key = question_keys[0]
            answers = request.POST.getlist(question_key)
        else:
            answers = []

        if answers:
            for answer in answers:
                existing_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, answerId=answer, dateAnswer=today_date).first()

                if existing_answer:
                    print(f"Answer already exists for userId: {user_id}, questionId: {question_id}, answerId: {answer}, no update needed.")
                else:
                    # Se la risposta non esiste (cioè, answerId diverso), aggiorna il valore
                    AnsweredQuestions.objects.update_or_create(
                        userId=user_id,
                        dateAnswer=today_date,
                        questionId=question_id,
                        answerId=answer,  # Usa answerId come chiave
                        defaults={'customAnswer': None}  # Aggiorna con il nuovo valore (se necessario)
                    )
                
        elif custom_answer:
            existing_answer_custom = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, dateAnswer=today_date, answerId=None).first()
            # Solo risposta custom, aggiorna o crea una singola risposta
            if existing_answer_custom:
                # Se esiste una risposta custom, aggiorna il campo customAnswer
                existing_answer_custom.customAnswer = custom_answer
                existing_answer_custom.save()  # Salva l'istanza aggiornata
            else:
                # Se non esiste una risposta custom, creane una nuova
                AnsweredQuestions.objects.create(
                    userId=user_id,
                    questionId=question_id,
                    answerId=None,
                    customAnswer=custom_answer
                )
        else:
            pass
    return render(request, 'questionnaire/result.html')


def test_start(request):
    return render(request, 'questionnaire/test_start.html')

def nextQuestion(request):
    today_date = datetime.date.today()
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Action: {action}")
        
        # Ottieni userId e questionId
        user_id = request.POST.get('userId')
        question_id = request.POST.get('questionId')

        # Calcola il numero totale di domande e domande completate
        total_questions = Question.objects.count()  # Numero totale di domande  AGGIUNGERE QUESTIONID
        questions_completed = AnsweredQuestions.objects.filter(userId=user_id, dateAnswer=today_date).count()  # Domande completate  AGGIUNGERE FILTRO PER DATA
        completion_percentage = (questions_completed / total_questions) * 100 if total_questions > 0 else 0  # Percentuale di completamento

        # Gestisci il caso del pulsante "Next"
        if action == 'next':
            is_generalita = request.POST.get('is_generalita', None)
            if is_generalita == 'true':
                # Preleva le risposte per le domande generali (età, peso, altezza, etc.)
                age = request.POST.get('age')
                weight = request.POST.get('weight')
                genderId = request.POST.get('gender')
                height = request.POST.get('height')
                waist = request.POST.get('waist_circum')
                smokeId = request.POST.get('smoke')

                # Salvataggio delle risposte per le domande con Custom Answer
                for questionid, answer_value in [(227, age), (228, weight), (229, height), (230, waist)]:
                    existing_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=questionid, dateAnswer=today_date).first()
                    if existing_answer:
                        existing_answer.customAnswer = answer_value
                        existing_answer.save()
                        print(f"Updated customAnswer for question {questionid}")
                    else:
                        AnsweredQuestions.objects.create(
                            userId=user_id,
                            questionId=questionid,
                            answerId=None,
                            customAnswer=answer_value
                        )
                        print(f"Created new answer for question {questionid}")

                # Aggiorna o crea risposte per "Sesso" e "Fumo"
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    dateAnswer=today_date,
                    defaults={'answerId': genderId},
                    questionId=226,
                )
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    dateAnswer=today_date,
                    defaults={'answerId': smokeId},
                    questionId=231,
                )

            # Gestione delle risposte alle domande successive
            question_keys = [k for k in request.POST.keys() if k.startswith("question_")]
            custom_answer = request.POST.get(f'customAnswer_{question_id}', None) 
            uploaded_file = request.FILES.get('file_upload')
           
            # Se il file è presente, salvalo nel modello
            if uploaded_file:
                # Cambio nome del file 
                original_filename = uploaded_file.name
                filename_without_extension, file_extension = os.path.splitext(original_filename)
                upload_file_date = datetime.date.today().strftime('%Y%m%d') 
                new_filename = f"{question_id}_{filename_without_extension}-{user_id}-{upload_file_date}{file_extension}"
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,  
                    dateAnswer=today_date,
                    questionId=question_id, 
                    defaults={'uploaded_file':  new_filename}  # Usa 'defaults' per aggiornare il campo 'uploaded_file'
                )

            # Gestisci le risposte multiple
            if question_keys:
                question_key = question_keys[0]
                answers = request.POST.getlist(question_key)
                print(f"Answers: {answers}")
            else:
                answers = []

            print(f"Answers: {answers}")

            if answers:
                # Cancella risposte esistenti per userId e questionId
                AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id,  dateAnswer=today_date).delete()
                print(f"Deleted existing answers for userId: {user_id}, questionId: {question_id}")
                
                # Crea nuove risposte
                for answer in answers:
                    AnsweredQuestions.objects.create(
                        userId=user_id,
                        questionId=question_id,
                        answerId=answer,
                    )
                    print(f"Created answer {answer} for question {question_id}")
                    
            elif custom_answer:
                # Gestisci le risposte personalizzate
                existing_answer_custom = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, answerId=None,  dateAnswer=today_date).first()
                if existing_answer_custom:
                    existing_answer_custom.customAnswer = custom_answer
                    existing_answer_custom.save()  # Salva l'istanza aggiornata
                    print(f"Updated customAnswer for question {question_id}")
                else:
                    AnsweredQuestions.objects.create(
                        userId=user_id,
                        questionId=question_id,
                        answerId=None,
                        customAnswer=custom_answer
                    )
                    print(f"Created new custom answer for question {question_id}")
            else:
                print("No answers or custom answer found.")

            # Recupera la prossima domanda
            nextQuestionObj, nextAnswer, nextDescription, is_last = getNextQuestion(question_id)
            print(f"is last: {is_last}")
            if nextQuestionObj is None:
                return redirect('result')

            # Prepara il context per la prossima domanda
            question = nextQuestionObj
            q = {
                'questionId': question.questionId,
                'description': question.description,
                'typeQuestion_description': question.typeQuestion_description,
                'typeQuestion_id': question.typeQuestion_idTypeQuestion,
                'groupId': question.groupId,
                'order': question.order,
            }
            answ = []
            for answer in nextAnswer:
                answ.append({
                    'answerId': answer.answerId,
                    'description': answer.description,
                    'order': answer.order
                })
            q['answers'] = answ

            context_questions = {
                'q': q,
                'questionId': q['questionId'],
                'userId': user_id,
                'is_last_question': is_last,
                'completion_percentage': completion_percentage
            }
            print(q['typeQuestion_id'])

            # Ritorna il template corretto in base al tipo domanda
            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_specifica.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_singola.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_media.html', context=context_questions)
            else:
                return render(request, 'questionnaire/result.html', {'userId': user_id})
        
        # Gestisci il caso del pulsante "Prev"
        elif action == 'prev':

            # Recupera la domanda precedente e la progress bar aggiornata
            previousQuestionObj, previousAnswer, is_first_group = getPreviousQuestion(question_id)

            if previousQuestionObj is None:
                return render(request, 'questionnaire/result.html', {'userId': user_id})

            if is_first_group:
                context_questions = showGeneralitaForm(user_id)
                return render(request, 'questionnaire/test_generale.html', context=context_questions)

            question = previousQuestionObj
            saved_answers = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId,  dateAnswer=today_date)
            saved_answer_ids = set(str(a.answerId) for a in saved_answers if a.answerId is not None)
            saved_custom_answer = None
            custom_answers = [a.customAnswer for a in saved_answers if a.customAnswer]
            if custom_answers:
                saved_custom_answer = custom_answers[0]

            q = {
                'questionId': question.questionId,
                'description': question.description,
                'typeQuestion_description': question.typeQuestion_description,
                'typeQuestion_id': question.typeQuestion_idTypeQuestion,
                'groupId': question.groupId,
                'order': question.order,
            }
            answ = []
            for answer in previousAnswer:
                answ.append({
                    'answerId': answer.answerId,
                    'description': answer.description,
                    'order': answer.order
                })
            q['answers'] = answ

            context_questions = {
                'q': q,
                'questionId': q['questionId'],
                'userId': user_id,
                'saved_answer_ids': saved_answer_ids,
                'saved_custom_answer': saved_custom_answer,
                'completion_percentage': completion_percentage  # Mostra la percentuale anche nel caso di "Prev"
            }

            # Ritorna il template adatto per la domanda precedente
            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_specifica.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_singola.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_media.html', context=context_questions)
            else:
                return render(request, 'questionnaire/result.html', {'userId': user_id})

    else:
        return redirect('home')
