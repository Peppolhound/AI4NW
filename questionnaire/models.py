from django.db import models
from django.conf import settings

# Create your models here.
class Questionnaire(models.Model):
    questionnaireId = models.CharField(max_length=100, unique=True)
    questionnaireName = models.CharField(max_length=100)
    dateInsert = models.DateTimeField(auto_now_add=True)
    # evaluatorClass = models.CharField(max_length=100, default="Evaluator")

    def __str__(self):
        return self.questionnaireName

class Group(models.Model):
    groupId = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=100)
    questionnaireId = models.CharField(max_length=100)
    order = models.IntegerField(default=0)  # Order of the group in the questionnaire

    def __str__(self):
        return self.description
    
class Question(models.Model):
    # question_questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questionQuestionnaire')
    questionId = models.CharField(max_length=100, unique=True)
    groupId = models.CharField(max_length=100)
    typeQuestion_idTypeQuestion = models.CharField(max_length=100)
    typeQuestion_description = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    order = models.IntegerField(default=0)  # Order of the question in the questionnaire
    
    def __str__(self):
        return self.description

class Answer(models.Model):
    answerId = models.CharField(max_length=100, unique=True)
    questionId = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    order = models.IntegerField(default=0)  # Order of the answer in the question
    # custom_answer = models.TextField(blank=True, null=True)  # Custom answer for open-ended questions
    
    def __str__(self):
        return self.description
    
class QuestionnaireValue(models.Model):
    questionnaireId = models.CharField(max_length=100)
    dateInsert = models.DateTimeField(auto_now_add=True)

class AnsweredQuestions(models.Model):
    userId = models.CharField(max_length=100)
    answerId = models.CharField(max_length=100, blank=True, null=True)
    questionId = models.CharField(max_length=100)
    customAnswer = models.CharField(max_length=2000, blank=True, null=True)  # Custom answer for open-ended questions
    dateAnswer = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.FileField(blank=True, null=True)
