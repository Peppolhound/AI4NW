from django.shortcuts import render, redirect
from .utils import *
from .models import Questionnaire, Group, Question, Answer, QuestionnaireValue, AnsweredQuestions
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
            # # Cancella risposte esistenti per userId e questionId prima di aggiornare le risposte
            # AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id).delete()
            # print(f"Deleted existing answers for userId: {user_id}, questionId: {question_id}")
            
            # # Crea nuove risposte
            # for answer in answers:
            #     AnsweredQuestions.objects.create(
            #         userId=user_id,
            #         questionId=question_id,
            #         answerId=answer,
            #         # defaults={'customAnswer': None}
            #     )
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
        # resto del codice
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
                for question_id, answer_value in [(227, age), (228, weight), (229, height), (230, waist)]:
                    existing_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question_id).first()
                    if existing_answer:
                        existing_answer.customAnswer = answer_value
                        existing_answer.save()  # Salva la risposta aggiornata
                    else:
                        AnsweredQuestions.objects.create(
                            userId=user_id,
                            questionId=question_id,
                            answerId=None,
                            customAnswer=answer_value
                        )
                        print(f"Created new answer for question {question_id}")

                # Aggiorna o crea le risposte per "Sesso" e "Fumo"
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    defaults= {'answerId': genderId},
                    questionId=226,
                )
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    defaults= {'answerId': smokeId},
                    questionId=231,
                )



    
            question_keys = [k for k in request.POST.keys() if k.startswith("question_")]
            custom_answer = request.POST.get(f'customAnswer_{question_id}', None)
            question_id = request.POST.get('questionId')
            

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

            # Recupera la prossima domanda
            nextQuestionObj, nextAnswer, nextDescription, is_last = getNextQuestion(question_id)
            print(f"is last: {is_last}")
            if nextQuestionObj is None:
                # È l'ultima domanda, quindi renderizza la pagina risultato
                return render(request, 'questionnaire/result.html', {'userId': user_id})
            
        

            # Altrimenti prepariamo il context per la prossima domanda
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
                return render(request, 'questionnaire/test_singola.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_specifica.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_checkbox.html', context=context_questions)
            else:
                # fallback (opzionale)
                return redirect('home')
            

        else:
            user_id = request.POST.get('userId')
            question_id = request.POST.get('questionId')
            previousQuestionObj, previousAnswer, is_first = getPreviousQuestion(question_id)
            print(f"Previous Question: {previousQuestionObj}")
            print(f"Answers: {previousAnswer}")
            print(f"Is first question in Anamnesi group: {is_first}")

            if previousQuestionObj is None:
                # È l'ultima domanda, quindi renderizza la pagina risultato
                return redirect('home')

            # Altrimenti prepariamo il context per la prossima domanda
            question = previousQuestionObj

            # Prendiamo tutte le risposte salvate per l'utente e la domanda corrente ed estraiamo gli indici delle risposte selezionate
            saved_answers = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId)
            print(f"Saved answers: {saved_answers}")
            saved_answer_ids = set(str(a.answerId) for a in saved_answers if a.answerId is not None)
            # Se la risposta è "custom" (testo libero, numero, ecc.)
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
                # fallback (opzionale)
                return render(request, 'questionnaire/result.html', {'userId': user_id})

    else:
        return redirect('home')
        

