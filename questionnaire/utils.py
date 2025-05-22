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


def call_api(endpoint_url, payload=None, headers=None, method='GET'):
    try:
        if method.upper() == 'GET':
            response = requests.get(endpoint_url, headers=headers, params=payload)
        elif method.upper() == 'POST':
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
    userId = response['idUser'] if 'idUser' in response else None
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
    

def showGeneralitaForm(user_id):
    today_date = datetime.date.today()
    tokenId = loginApplicativo()
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

            saved_answer = AnsweredQuestions.objects.filter(userId=user_id, questionId=question.questionId, dateAnswer=today_date).first()
            if saved_answer:
                # Se c'è una risposta salvata, precompila il campo
                if saved_answer.answerId:
                    q['saved_answer'] = saved_answer.answerId
                elif saved_answer.customAnswer:
                    q['saved_answer'] = saved_answer.customAnswer

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
        context_questions['userId'] = user_id 
        return context_questions

def submitQuestionnaire(userId, questionnaireId):


    ##### RACCOGO ED ORGANIZZO IN JSON I DATI DEL QUESTIONARIO #####
    questionnaireResponse = {}
    file_list = []
    answer_list = []
    questionnaireValue = QuestionnaireValue.objects.get(questionnaireId=questionnaireId).first()
    questionnaireResponse['dateInsert'] = questionnaireValue.dateInsert
    questionnaireResponse['questionnaireKey'] = "NW"

    groups = Group.objects.filter(questionnaireId=questionnaireId)
    for group in groups:
        questions = Question.objects.filter(groupId=group.groupId)
        for question in questions:
            answers = AnsweredQuestions.objects.filter(questionId=question.questionId)
            answer_dict = {}
            for answer in answers:
                answer_dict['answerId'] = answer.answerId
                answer_dict['questionId'] = answer.questionId
                answer_dict['customAnswer'] = answer.customAnswer
                if answer.uploaded_file:
                    file_list.append(answer.uploaded_file)    # Se l'ID della risposta corrisponde a quello selezionato, salva la risposta
                answer_list.append(answer_dict)
    questionnaireResponse['answeredQuestions'] = answer_list

    ######### PREPARO LA CHIAMATA ALL'API #########
    endpoint_url = "https://vita-develop.health-portal.it/nw-ws/night-worker/questionnaire/"
    method = "POST"
    headers = {
        'Content-Type': 'application/json',
        'tokenId': loginApplicativo(),
    }
    payload = {
        "userId": userId,
        "questionnaire": questionnaireResponse,
        "files": file_list,
    }

    response = call_api(endpoint_url=endpoint_url, payload=payload, headers=headers, method=method)
    if response is not None:
        print("Questionnaire submitted successfully. {response}")
    else:
        print("Failed to submit questionnaire.")