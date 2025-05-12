import json
from questionnaire.models import Questionnaire, Group, Question, Answer

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