from django.shortcuts import render, redirect
from .utils import *
from .models import Questionnaire, Group, Question, Answer, QuestionnaireValue, AnsweredQuestions
from django.core.serializers import serialize
import json

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    return render(request, 'questionnaire/login.html')


def test(request):
    return render(request, 'questionnaire/test_start.html')

def test_generale(request):
    if request.method == 'POST':
        username = request.POST.get('login-info')
        # print(f"Nome: {nome}, Cognome: {cognome}, Data di Nascita: {birthdate}")
        usercode = getUserCode(username)
        # print(f"Usercode: {usercode}")
        tokenId = loginApplicativo()
        if tokenId is not None:
            ################## DEBUG ##################
            # usercode = '9876'                       
            ################## DEBUG ##################
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
                existing_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, answerId=answer).first()

                if existing_answer:
                    print(f"Answer already exists for userId: {user_id}, questionId: {question_id}, answerId: {answer}, no update needed.")
                else:
                    # Se la risposta non esiste (cioè, answerId diverso), aggiorna il valore
                    AnsweredQuestions.objects.update_or_create(
                        userId=user_id,
                        questionId=question_id,
                        answerId=answer,  # Usa answerId come chiave
                        defaults={'customAnswer': None}  # Aggiorna con il nuovo valore (se necessario)
                    )
                
        elif custom_answer:
            existing_answer_custom = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, answerId=None).first()
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
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Action: {action}")
        
        if action == 'next':
            is_generalita = request.POST.get('is_generalita', None)
            user_id = request.POST.get('userId')
            question_id = request.POST.get('questionId')
            
            if is_generalita == 'true':
                age = request.POST.get('age')
                weight = request.POST.get('weight')
                genderId = request.POST.get('gender')
                height = request.POST.get('height')
                waist = request.POST.get('waist_circum')
                smokeId = request.POST.get('smoke')
                
                # Salvataggio delle risposte per le domande generali (età, peso, altezza, etc.)
                for question_id, answer_value in [(227, age), (228, weight), (229, height), (230, waist)]:
                    existing_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id).first()
                    if existing_answer:
                        existing_answer.customAnswer = answer_value
                        existing_answer.save()
                        print(f"Updated customAnswer for question {question_id}")
                    else:
                        AnsweredQuestions.objects.create(
                            userId=user_id,
                            questionId=question_id,
                            answerId=None,
                            customAnswer=answer_value
                        )
                        print(f"Created new answer for question {question_id}")

                # Aggiorna o crea risposte per "Sesso" e "Fumo"
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    defaults={'answerId': genderId},
                    questionId=226,
                )
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    defaults={'answerId': smokeId},
                    questionId=231,
                )

            # Gestione delle risposte alle domande successive
            question_keys = [k for k in request.POST.keys() if k.startswith("question_")]
            custom_answer = request.POST.get(f'customAnswer_{question_id}', None)            
            print(f"Custom Answer: {custom_answer}")

            if question_keys:
                question_key = question_keys[0]
                answers = request.POST.getlist(question_key)
                print(f"Answers: {answers}")
            else:
                answers = []

            print(f"Answers: {answers}")

            if answers: #Controllo risposte multiple, salvale nel database
                # Cancella risposte esistenti per userId e questionId
                AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id).delete()
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
                existing_answer_custom = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id, answerId=None).first()
                if existing_answer_custom:
                    # Se esiste una risposta custom, aggiorna il campo customAnswer
                    existing_answer_custom.customAnswer = custom_answer
                    existing_answer_custom.save()  # Salva l'istanza aggiornata
                    print(f"Updated customAnswer for question {question_id}")
                else:
                    # Se non esiste una risposta custom, creane una nuova
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
            if nextQuestionObj is None:
                # È l'ultima domanda, quindi renderizza la pagina risultato
                return render(request, 'questionnaire/result.html', {'userId': user_id})

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
                'is_last_question': is_last
            }

            # Ritorna il template adatto in base al tipo domanda
            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_specifica.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_singola.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            else:
                # fallback (opzionale)
                return render(request, 'questionnaire/result.html', {'userId': user_id})
        else:
            user_id = request.POST.get('userId')
            question_id = request.POST.get('questionId')
            previousQuestionObj, previousAnswer, is_first_group = getPreviousQuestion(question_id)


            if previousQuestionObj is None:
                # È l'ultima domanda, quindi renderizza la pagina risultato
                return render(request, 'questionnaire/result.html', {'userId': user_id})

            if is_first_group:
                context_questions = showGeneralitaForm(user_id)
                return render(request, 'questionnaire/test_generale.html', context=context_questions)


            # Prepara il context per la prossima domanda
            question = previousQuestionObj
            saved_answers = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId)
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
            }

            # Ritorna il template adatto in base al tipo domanda
            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_specifica.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_singola.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            else:
                return render(request, 'questionnaire/result.html', {'userId': user_id})

    else:
        return redirect('home')
