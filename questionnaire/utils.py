import json
from questionnaire.models import Questionnaire, Group, Question, Answer, AnsweredQuestions, QuestionnaireValue
import requests
import datetime

def parseJSON(json_string):

    data = json_string

    # Create Questionnaire
    questionnaire, _ = Questionnaire.objects.update_or_create(
        questionnaireId=data['questionnaireId'],
        defaults={
            'questionnaireName':data['questionnaireName'],
            'dateInsert':data['dateInsert']},
        )

    # Iterate through groups
    for group_data in data['groups']:
        group, _ = Group.objects.update_or_create(
            groupId=group_data['groupId'],
            defaults={
                'description':group_data['description'],
                'order':group_data['order'],
                'questionnaireId':questionnaire.questionnaireId,
                }
            )

        # Iterate through questions in the group
        for question_data in group_data['questions']:
            question, _ = Question.objects.update_or_create(
                questionId=question_data['questionId'],
                defaults={
                    'groupId':group.groupId,
                    'typeQuestion_idTypeQuestion':question_data['typeQuestion']['idTypeQuestion'],
                    'typeQuestion_description':question_data['typeQuestion']['description'],
                    'description':question_data['description'],
                    'order':question_data['order']
                },
            )

            # Iterate through answers in the question
            for answer_data in question_data.get('answers', []):  # question_data['answers'] might not exist
                Answer.objects.update_or_create(
                    answerId=answer_data['answerId'],
                    defaults={
                        'questionId':question.questionId,
                        'description':answer_data['description'],
                        'order':answer_data['order']
                    }
                )
    
    return questionnaire


def call_api(endpoint_url, payload=None, headers=None, method='GET', files=None):
    try:
        if method.upper() == 'GET':
            response = requests.get(endpoint_url, headers=headers, params=payload)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(endpoint_url, headers=headers, data=payload, files=files)
            else:
                response = requests.post(endpoint_url, headers=headers, json=payload)
        elif method.upper() == 'PUT':
            response = requests.put(endpoint_url, headers=headers, json=payload)
        elif method.upper() == 'DELETE':
            response = requests.delete(endpoint_url, headers=headers, json=payload)
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def loginApplicativo():
    url = "https://vita-develop.health-portal.it/nw-ws/night-worker/auth/app-login"
    payload = {
        "username": "admin-nw",
        "password": "6jS3Fohz@C"
    }
    method = "POST"
    headers = {
        'Content-Type': 'application/json'
    }
    response = call_api(endpoint_url=url, payload=payload, headers=headers, method=method)
    tokenId = response['tokenId'] if 'tokenId' in response else None
    return tokenId

def loginUtente(userCode, tokenId):
    url = f"https://vita-develop.health-portal.it/nw-ws/night-worker/auth/user-login?userCode={userCode}"
    method = "POST"
    headers = {
        'Content-Type': 'application/json',
        'tokenId': tokenId,
    }
    response = call_api(endpoint_url=url, headers=headers, method=method)
    userId = response.get('idUser') if isinstance(response, dict) else None
    return userId

def getQuestionnaire(tokenId):
    url='https://vita-develop.health-portal.it/nw-ws/night-worker/questionnaire/NW'
    method = "GET"
    headers = {
        'Content-Type': 'application/json',
        'tokenId': tokenId,
    }
    questionnaierJSON = call_api(endpoint_url=url, headers=headers, method=method)
    if 'questionnaireId' in questionnaierJSON:
        return questionnaierJSON
    else:
        return None
    
def getUserCode(usercode):
    return usercode

def getNextQuestion(questionId):
    try:
        currentQuestion = Question.objects.get(questionId=questionId)
        print(f"Current Question: {currentQuestion.description}")
    except Question.DoesNotExist:
        print(f"No question found with ID: {questionId}")
        return None, None, None, True  # Nessuna domanda

    # STEP 1 - Cerca la prossima domanda nello stesso gruppo
    nextQuestion = Question.objects.filter(
        groupId=currentQuestion.groupId,
        order__gt=currentQuestion.order
    ).order_by('order').first()

    if nextQuestion:
        print(f"Next Question in the same group: {nextQuestion.description}")
        nextAnswers = Answer.objects.filter(questionId=nextQuestion.questionId).order_by('order')
        nextDescription = nextQuestion.typeQuestion_description

        # Controllo se questa domanda è l'ultima: se non c'è una domanda dopo nextQuestion
        is_last = not Question.objects.filter(
            groupId=nextQuestion.groupId,
            order__gt=nextQuestion.order
        ).exists() and not Group.objects.filter(
            questionnaireId=Group.objects.get(groupId=nextQuestion.groupId).questionnaireId,
            order__gt=Group.objects.get(groupId=nextQuestion.groupId).order
        ).exists()
        print(f"Is this the last question in the group? {is_last}")

        return nextQuestion, nextAnswers, nextDescription, is_last

    # STEP 2 - Nessuna domanda successiva in questo gruppo → cerca nel gruppo successivo
    try:
        currentGroup = Group.objects.get(groupId=currentQuestion.groupId)
        print(f"Current Group: {currentGroup.description}")
    except Group.DoesNotExist:
        print(f"No group found for question ID: {questionId}")
        return None, None, None, True

    # STEP 3 - Cerca il gruppo successivo
    nextGroup = Group.objects.filter(
        questionnaireId=currentGroup.questionnaireId,
        order__gt=currentGroup.order
    ).order_by('order').first()

    if not nextGroup:
        print("No next group found. This is the last group.")
        # Nessun gruppo successivo = ultima domanda
        return None, None, None, True

    print(f"Next Group: {nextGroup.description}")

    # STEP 4 - Trova la prima domanda del gruppo successivo
    nextQuestion = Question.objects.filter(groupId=nextGroup.groupId).order_by('order').first()
    if not nextQuestion:
        print(f"No questions in next group: {nextGroup.description}")
        return None, None, None, True

    print(f"Next Question in next group: {nextQuestion.description}")
    nextAnswers = Answer.objects.filter(questionId=nextQuestion.questionId).order_by('order')
    nextDescription = nextQuestion.typeQuestion_description

    # Controlla se la domanda successiva è l'ultima nel questionario
    # Verifica se non ci sono altre domande dopo nextQuestion né gruppi dopo nextGroup
    is_last = not Question.objects.filter(
        groupId=nextQuestion.groupId,
        order__gt=nextQuestion.order
    ).exists() and not Group.objects.filter(
        questionnaireId=nextGroup.questionnaireId,
        order__gt=nextGroup.order
    ).exists()

    print(f"Is this the last question in the questionnaire? {is_last}")

    return nextQuestion, nextAnswers, nextDescription, is_last

def getPreviousQuestion(questionId):
    try:
        currentQuestion = Question.objects.get(questionId=questionId)
    except Question.DoesNotExist:
        return None, None, False
    
    # Trova la domanda precedente nel gruppo corrente
    previousQuestion = Question.objects.filter(groupId=currentQuestion.groupId, order__lt=currentQuestion.order).order_by('-order').first()

    is_first = False
    if previousQuestion:
        # Trova le risposte per la domanda precedente
        answers = Answer.objects.filter(questionId=previousQuestion.questionId).order_by('order')
        
        
        # Se la descrizione del gruppo precedente è "Anamnesi", imposta is_first a True
        if previousQuestion.groupId == "21":  # Confronta con la descrizione del gruppo
            is_first = True

        return previousQuestion, answers, is_first 
    else:
        # Se non c'è una domanda precedente, cerca il gruppo precedente
        currentGroup = Group.objects.get(groupId=currentQuestion.groupId)
        previousGroup = Group.objects.filter(questionnaireId=currentGroup.questionnaireId, order__lt=currentGroup.order).order_by('-order').first()
        
        if previousGroup:
            previousQuestion = Question.objects.filter(groupId=previousGroup.groupId).order_by('-order').first()
            if previousQuestion:
                answers = Answer.objects.filter(questionId=previousQuestion.questionId).order_by('order')

                # Imposta is_first a True solo se la domanda precedente appartiene al gruppo "Anamnesi"
                if previousGroup.description == "Anamnesi":  # Confronta con la descrizione del gruppo
                    is_first = True
                return previousQuestion, answers, is_first
            else:
                # Se non ci sono domande nel gruppo precedente, restituisci None
                return None, None, is_first
        else:
            return None, None, is_first
        
        
def getFirstQuestion(questionnaireId):
    try:
        firstGroup = Group.objects.filter(questionnaireId=questionnaireId).order_by('order').first()
        if firstGroup:
            firstQuestion = Question.objects.filter(groupId=firstGroup.groupId).order_by('order').first()
            answers = Answer.objects.filter(questionId=firstQuestion.questionId).order_by('order')
            return firstQuestion, answers
        else:
            return None
    except Group.DoesNotExist:
        return None
    

def showGeneralitaForm(user_id, usercode, questionnaireJSON):
    today_date = datetime.date.today()

    # print(f"Questionnaire JSON: {questionnaireJSON}")
    if questionnaireJSON is not None:
        questionnaire = parseJSON(questionnaireJSON)
        first_group = Group.objects.filter(questionnaireId=questionnaire.questionnaireId).order_by('order').first() # SELEZIONO IL PRIMO GRUPPO con ID del questionario (in genere ANAMNESI)
        questions = Question.objects.filter(groupId=first_group.groupId).order_by('order')              # SELEZIONO LE DOMANDE del primo gruppo
        # print(f"Questions: {questions}")

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
            

            saved_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId, dateAnswer=today_date).first()
            if saved_answer:
                # Se c'è una risposta salvata, precompila il campo
                if saved_answer.answerId:
                    q['saved_answer'] = saved_answer.answerId
                elif saved_answer.customAnswer:
                    q['saved_answer'] = saved_answer.customAnswer

            if 'Sesso' in question.description: 
                context_questions['sesso'] = q
                # context_questions['questionId'] = q['questionId'] 
            elif 'Età' in question.description:
                context_questions['eta'] = q
                # context_questions['questionId'] = q['questionId'] 
            elif 'Altezza' in question.description:
                context_questions['altezza'] = q
                # context_questions['questionId'] = q['questionId'] 
            elif 'Peso' in question.description:
                context_questions['peso'] = q
                # context_questions['questionId'] = q['questionId'] 
            elif 'Fumi?' in question.description:
                context_questions['fumo'] = q
                # context_questions['questionId'] = q['questionId'] 
            elif 'Addominale' in question.description:
                context_questions['addominale'] = q
                # context_questions['questionId'] = q['questionId'] 

        # User login failed, show an error message
        question_id = context_questions['fumo']['questionId']
        context_questions['questionId'] = question_id
        completion_percentage = getProgressBarStatus(questionnaire.questionnaireId, question_id)
        context_questions['completion_percentage'] = completion_percentage




        context_questions['questionnaireId'] = questionnaire.questionnaireId
        context_questions['userId'] = user_id 
        context_questions['userCode'] = usercode
        context_questions['description'] = "GENERALITÀ"
        print(f"Context Questions: {context_questions}")
        return context_questions

import json
import datetime

def submitQuestionnaire(userId, userCode, questionnaireId):
    # === RACCOLTA DATI ===
    questionnaireResponse = {}
    file_list = []
    answer_list = []
    today = datetime.date.today()

    print(f"Today: {today}")
    print(f"User ID: {userId}")
    print(f"Questionnaire ID: {questionnaireId}")
    
    questionnaireValue = QuestionnaireValue.objects.get(questionnaireId=questionnaireId, user_id=userId, dateInsert=today)
    questionnaireResponse['dateInsert'] = int(questionnaireValue.dateInsert.strftime("%Y%m%d"))
    questionnaireResponse['questionnaireKey'] = "NW"

    groups = Group.objects.filter(questionnaireId=questionnaireId)
    for group in groups:
        questions = Question.objects.filter(groupId=group.groupId)
        for question in questions:
            answers = AnsweredQuestions.objects.filter(questionId=question.questionId, userId=userId, dateAnswer=today)
            for answer in answers:
                answer_dict = {
                    'answerId': int(answer.answerId) if answer.answerId else None,
                    'questionId': int(answer.questionId) if answer.questionId else None,
                    'customAnswer': answer.customAnswer,
                }
                if answer.uploaded_file:
                    file_list.append(answer.uploaded_file)
                answer_list.append(answer_dict)
    
    questionnaireResponse['answeredQuestions'] = answer_list

    # === CONVERSIONE A FORM DATA MULTIPART ===
    endpoint_url = f"https://vita-develop.health-portal.it/nw-ws/night-worker/questionnaire/submit?idUser={userId}"
    headers = {
        'tokenId': loginApplicativo(),
    }

    # FORM DATA
    files = []

    # Parte 1: JSON come stringa in un campo 'questionnaire'
    files.append(('questionnaire', (None, json.dumps(questionnaireResponse), 'application/json')))

    # Parte 2: allegati
    for f in file_list:
        files.append(('files', (f.name.split('/')[-1], f.open('rb'), 'image/jpeg')))

    print(f'JSON: {files}')
    # Invio della richiesta POST multipart
    import requests
    response = call_api(endpoint_url=endpoint_url, headers=headers, method='POST', files=files)
    # response = requests.post(endpoint_url, headers=headers, files=files)

    # === GESTIONE RISPOSTA ===
    if response:
        print("Questionnaire submitted successfully.")
    else:
        print(f"Failed to submit questionnaire.")
    return response


def getSavedAnswers(userId, questionId):
    today = datetime.date.today()
    saved_answers = AnsweredQuestions.objects.filter(
        userId=userId,
        questionId=questionId,
        dateAnswer=today
    )

    saved_answer_ids = set()
    saved_custom_answer = None
    uploaded_files = []

    if saved_answers.exists():
        # Raccolta degli answerId (es. per domande a risposta chiusa)
        saved_answer_ids = set(str(a.answerId) for a in saved_answers if a.answerId)

        # Risposta custom (una sola gestita)
        custom_answers = [a.customAnswer for a in saved_answers if a.customAnswer]
        if custom_answers:
            saved_custom_answer = custom_answers[0]

        # Raccolta dei file caricati
        uploaded_files = [a.uploaded_file for a in saved_answers if a.uploaded_file]

    print(f"Files: {[f.name for f in uploaded_files]}")
    return saved_answer_ids, saved_custom_answer, uploaded_files

def getProgressBarStatus(questionnaireId, questionId):

    # Calcola il numero totale di domande 
    groupsID = Group.objects.filter(questionnaireId=questionnaireId).values_list('groupId', flat=True)
    total_questions = Question.objects.filter(groupId__in=groupsID).count()  # Numero totale di domande  AGGIUNGERE QUESTIONID

    # Calcola il numero di domande fino alla domanda corrente
    questionList = []
    for group in groupsID:
        questionList.extend(list(Question.objects.filter(groupId=group).order_by('order').values_list('questionId', flat=True)))

    print(f"QuestionList: {questionList}")
    try:
        idx = questionList.index(questionId)
        # print(f"Index of current question: {idx}")
        # print(f"Question ID: {questionId}")
        questions_completed = idx + 1
    except ValueError:
        questions_completed = 0
    print(f"Total questions: {total_questions}")
    print(f"Questions completed: {questions_completed}")
    completion_percentage = (questions_completed / total_questions) * 100 if total_questions > 0 else 0  # Percentuale di completamento

    return completion_percentage