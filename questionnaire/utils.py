import json
from questionnaire.models import Questionnaire, Group, Question, Answer
import requests

def parseJSON(json_string):

    data = json.loads(json_string)

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
    return print("Data parsed and saved successfully.") 


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