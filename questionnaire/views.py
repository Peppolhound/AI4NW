from django.shortcuts import render, redirect
from AI4NW import settings
from .utils import *
from .models import Questionnaire, Group, Question, Answer, QuestionnaireValue, AnsweredQuestions
from django.core.files.storage import FileSystemStorage
from django.core.serializers import serialize
import datetime
import os
import json
from django.utils import timezone

# Create your views here.
def home(request):
    return render(request, 'questionnaire/home.html')

def login(request):
    # questionnaireId = Questionnaire.objects.first().questionnaireId
    # print(f"questionnaireId: {questionnaireId}") # stampa il valore di questionnaireId)
    # return render(request, 'questionnaire/login.html', {'questionnaireId': questionnaireId})
    return render(request, 'questionnaire/login.html')


def test(request):
    return render(request, 'questionnaire/test_start.html')

def test_intro(request):
    if request.method == 'POST':
        username = request.POST.get('login-info')
        usercode = getUserCode(username)
        tokenId = loginApplicativo()
        if tokenId is not None:
            ################## DEBUG ##################
            # usercode = '9876'                       
            ################## DEBUG ##################
            questionnaireJSON = getQuestionnaire(tokenId)
            questionnaireId = questionnaireJSON['questionnaireId']
            print(f"Questionnaire ID: {questionnaireId}")
            user_id= loginUtente(usercode, tokenId)
            if user_id:
                QuestionnaireValue.objects.update_or_create(
                    user_id=user_id,
                    questionnaireId=questionnaireId,
                    dateInsert=datetime.date.today(),
                )
                context_questions = showGeneralitaForm(user_id, usercode, questionnaireJSON)
                return render(request, 'questionnaire/test_intro.html', context=context_questions)
            else:
                return render(request, 'questionnaire/login.html', {'error_message': 'Indirizzo email o codice di accesso non valido. Riprova.'})
    else:
        # If it's a GET request, just render the login page
        return redirect('login')
    
# def test_singola(request):
#     return render(request, 'questionnaire/test_singola.html')

# def test_checkbox(request):
#     return render(request, 'questionnaire/test_checkbox.html')

# def test_specifica(request):
#     return render(request, 'questionnaire/test_specifica.html')

def result(request):
    today_date = datetime.date.today()
    if request.method == 'POST':
        question_keys = [k for k in request.POST.keys() if k.startswith("question_")]
        question_id = request.POST.get('questionId')
        custom_answer = request.POST.get(f'customAnswer_{question_id}', None)
        user_id = request.POST.get('userId')    
        user_code = request.POST.get('userCode')
        questionnaireId = request.POST.get('questionnaireId')
        

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
        
        response = submitQuestionnaire(userId=user_id, userCode = user_code, questionnaireId=questionnaireId)
        print(f"Response: {response}")

        cmds_uomo = response['results'].get('CDMS (uomo)', '')
        cmds_donna = response['results'].get('CDMS (donna)', '')
        if cmds_uomo and cmds_donna:
            cmds = f"<strong>Uomo:</strong> <em>{cmds_uomo}</em><br><strong>Donna:</strong> <em>{cmds_uomo}</em>"
        elif cmds_uomo and not cmds_donna:
            cmds = f"<em>{cmds_uomo}</em>"
        elif cmds_donna and not cmds_uomo:
            cmds = f"<em>{cmds_donna}</em>"
        else:
            cmds = ""

        framingham_uomo = response['results'].get('Framingham Risk (uomo)', '')
        framingham_donna = response['results'].get('Framingham Risk (donna)', '')
        if framingham_uomo and framingham_donna:
            framingham = f"<strong>Uomo:</strong> <em>{framingham_uomo}</em><br><strong>Donna:</strong> <em>{framingham_donna}</em>"
        elif framingham_uomo and not framingham_donna:
            framingham = f"<em>{framingham_uomo}</em>"
        elif framingham_donna and not framingham_uomo:
            framingham = f"<em>{framingham_donna}</em>"
        else:
            framingham = ""

        if response:
            context = {
                'CMDS': cmds,
                'Framingham': framingham,   
            }
        else:
            print(f"Error! Response = None")
            context = {
                'error_message': 'Errore durante l\'invio del questionario. Riprova più tardi.',
            }
        return render(request, 'questionnaire/result.html', context=context)


def test_start(request):
    return render(request, 'questionnaire/test_start.html')

def nextQuestion(request):
    today_date = timezone.now().date()
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Action: {action}")
        
        # Ottieni userId e questionId
        user_id = request.POST.get('userId')
        user_code = request.POST.get('userCode')
        print(f"User ID: {user_id}")
        print(f"User code: {user_code}")
        question_id = request.POST.get('questionId')
        questionnaireId = request.POST.get('questionnaireId')
        print(f'questionnaireId: {questionnaireId}')
        print(f'questionId: {question_id}')
        print(f'userId: {user_id}')

        # # Calcola il numero totale di domande e domande completate
        # groupsID = Group.objects.filter(questionnaireId=questionnaireId).values_list('groupId', flat=True)
        # total_questions = Question.objects.filter(groupId__in=groupsID).count()  # Numero totale di domande  AGGIUNGERE QUESTIONID
        # print(f"Total questions: {total_questions}")
        # questions_completed = AnsweredQuestions.objects.filter(userId=user_id, dateAnswer=today_date).count()  # Domande completate nelle ultime ore
        # print(f"Questions completed: {questions_completed}")
        # completion_percentage = (questions_completed / total_questions) * 100 if total_questions > 0 else 0  # Percentuale di completamento

        completion_percentage = getProgressBarStatus(questionnaireId, question_id)
        stringQuestions = ["241"]


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
                    AnsweredQuestions.objects.update_or_create(
                        dateAnswer=today_date,
                        userId=user_id,
                        questionId=questionid,
                        answerId=None,
                        defaults={'customAnswer': answer_value},
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
            uploaded_file = request.FILES.getlist('file_upload')



            if uploaded_file:
                # Cancella eventuali file precedenti per la stessa domanda, stesso utente e stessa data
                AnsweredQuestions.objects.filter(
                    userId=user_id,
                    questionId=question_id,
                    dateAnswer=datetime.date.today()
                ).delete()

                for i, file in enumerate(uploaded_file):
                    original_filename = file.name
                    filename_without_extension, file_extension = os.path.splitext(original_filename)
                    upload_file_date = datetime.date.today().strftime('%Y%m%d') 
                    new_filename = f"{question_id}_{filename_without_extension}-{user_id}-{upload_file_date}{file_extension}"
                    file.name = new_filename

                    AnsweredQuestions.objects.create(
                        userId=user_id,
                        questionId=question_id,
                        customAnswer=custom_answer if custom_answer else None,
                        dateAnswer=datetime.date.today(),
                        uploaded_file=file  # salva ogni file come nuova entry, se vengono inseriti 2 file insieme si duplica la domanda
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
                AnsweredQuestions.objects.update_or_create(
                    userId=user_id,
                    questionId=question_id,
                    answerId=None,
                    dateAnswer=today_date,
                    defaults={'customAnswer':custom_answer},
                )
                print(f"Created new custom answer for question {question_id}")
            else:
                print("No answers or custom answer found.")

            # Recupera la prossima domanda
            nextQuestionObj, nextAnswer, nextDescription, is_last = getNextQuestion(question_id)
            # if nextQuestionObj is None:
            #     return render(request, 'questionnaire/result.html', {'userId': user_id})


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

            saved_answer_ids, saved_custom_answer, uploaded_file = getSavedAnswers(user_id, question.questionId)


            if question.questionId in stringQuestions:
                is_numeric = False
            else:
                is_numeric = True


            context_questions = {
                'q': q,
                'questionId': q['questionId'],
                'description':  Group.objects.get(groupId=question.groupId),
                'questionnaireId': questionnaireId,
                'userId': user_id,
                'is_last_question': is_last,
                'saved_answer_ids': saved_answer_ids,
                'saved_custom_answer': saved_custom_answer,
                'uploaded_file': uploaded_file, 
                'userCode' : user_code,
                'completion_percentage': completion_percentage,
                'is_numeric': is_numeric,  
            }
            print(f'La prossima domanda sarà {q["typeQuestion_description"]}')
            print(f'Questionnaire ID_casonext: {questionnaireId}')

            # Ritorna il template corretto in base al tipo domanda
            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_radio.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_text.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_check.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_media.html', context=context_questions)
            else:
                return render(request, 'questionnaire/result.html', {'userId': user_id})
        



        # Gestisci il caso del pulsante "Prev"
        elif action == 'prev':
            print("Prev button clicked")
            # Recupera la domanda precedente e la progress bar aggiornata
            previousQuestionObj, previousAnswer, is_first_group = getPreviousQuestion(question_id)

            # if previousQuestionObj is None:
            #     return render(request, 'questionnaire/result.html', {'userId': user_id, 'userCode': user_code})

            if is_first_group:
                questionnaireJSON = getQuestionnaire(loginApplicativo())
                context_questions = showGeneralitaForm(user_id, user_code, questionnaireJSON)
                return render(request, 'questionnaire/test_intro.html', context=context_questions)

            question = previousQuestionObj
            # saved_answers = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId,  dateAnswer=today_date)
            # saved_answer_ids = set(str(a.answerId) for a in saved_answers if a.answerId is not None)
            # saved_custom_answer = None
            # custom_answers = [a.customAnswer for a in saved_answers if a.customAnswer]
            # if custom_answers:
            #     saved_custom_answer = custom_answers[0]
            saved_answer_ids, saved_custom_answer, uploaded_file = getSavedAnswers(user_id, question.questionId)

            completion_percentage = getProgressBarStatus(questionnaireId, question_id)

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

            if question.questionId in stringQuestions:
                is_numeric = False
            else:
                is_numeric = True

            context_questions = {
                'q': q,
                'questionId': q['questionId'],
                'description':  Group.objects.get(groupId=question.groupId),
                'userId': user_id,
                'questionnaireId': questionnaireId,
                'saved_answer_ids': saved_answer_ids,
                'userCode' : user_code,
                'saved_custom_answer': saved_custom_answer,
                'uploaded_file': uploaded_file, 
                'completion_percentage': completion_percentage,  # Mostra la percentuale anche nel caso di "Prev"
                'is_numeric': is_numeric,  # Aggiungi questa riga
            }
            print(f'Questionnaire ID_Casoprev: {questionnaireId}')

            # Ritorna il template adatto per la domanda precedente

            if q['typeQuestion_id'] == "1":
                return render(request, 'questionnaire/test_radio.html', context=context_questions)
            elif q['typeQuestion_id'] == "2":
                return render(request, 'questionnaire/test_text.html', context=context_questions)
            elif q['typeQuestion_id'] == "3":
                return render(request, 'questionnaire/test_check.html', context=context_questions)
            elif q['typeQuestion_id'] == "4":
                return render(request, 'questionnaire/test_media.html', context=context_questions)
            else:
                return render(request, 'questionnaire/result.html', {'userId': user_id})
    else:
        return redirect('home')

def scarica(request):
    return render(request, 'questionnaire/scarica.html')