import json
from questionnaire.models import Questionnaire, Group, Question, Answer
import requests

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
    except Question.DoesNotExist:
        return None, None, None

    print(f"➡️ Domanda corrente: {currentQuestion.description} (ID: {currentQuestion.questionId}, gruppo: {currentQuestion.groupId}, ordine: {currentQuestion.order})")

    # STEP 1 - Cerca la prossima domanda nello stesso gruppo
    nextQuestion = Question.objects.filter(
        groupId=currentQuestion.groupId,
        order__gt=currentQuestion.order
    ).order_by('order').first()

    if nextQuestion:
        nextAnswers = Answer.objects.filter(questionId=nextQuestion.questionId).order_by('order')
        nextDescription = nextQuestion.typeQuestion_description
        return nextQuestion, nextAnswers, nextDescription

    # STEP 2 - Nessuna domanda successiva in questo gruppo → cerca nel gruppo successivo
    try:
        currentGroup = Group.objects.get(groupId=currentQuestion.groupId)
    except Group.DoesNotExist:
        return None, None, None


    # STEP 3 - Cerca il gruppo successivo
    nextGroup = Group.objects.filter(
        questionnaireId=currentGroup.questionnaireId,
        order__gt=currentGroup.order
    ).order_by('order').first()

    if not nextGroup:
        return None, None, None

    # STEP 4 - Trova la prima domanda del gruppo successivo
    nextQuestion = Question.objects.filter(groupId=nextGroup.groupId).order_by('order').first()
    if not nextQuestion:
        return None, None, None

    nextAnswers = Answer.objects.filter(questionId=nextQuestion.questionId).order_by('order')
    nextDescription = nextQuestion.typeQuestion_description

    return nextQuestion, nextAnswers, nextDescription



def getPreviousQuestion(questionId):
    try:
        currentQuestion = Question.objects.get(questionId=questionId)
    except Question.DoesNotExist:
        return None
    
    previousQuestion = Question.objects.filter(groupId=currentQuestion.groupId, order__lt=currentQuestion.order).order_by('-order').first()

    if previousQuestion:
        answers = Answer.objects.filter(questionId=previousQuestion.questionId).order_by('order')
        return previousQuestion, answers
    else:
        # If no previous question, return the last question of the previous group
        currentGroup = Group.objects.get(groupId=currentQuestion.groupId)
        previousGroup = Group.objects.filter(questionnaireId=currentGroup.questionnaireId, order__lt=currentGroup.order).order_by('-order').first()
        if previousGroup:
            previousQuestion = Question.objects.filter(groupId=previousGroup.groupId).order_by('-order').first()
            if previousQuestion:
                answers = Answer.objects.filter(questionId=previousQuestion.questionId).order_by('order')
                return previousQuestion, answers
            else:
                # If no questions in the previous group, return None
                return None
        else:
            return None
        
        
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