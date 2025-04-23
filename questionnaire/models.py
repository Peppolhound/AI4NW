from django.db import models

# Create your models here.
class Questionnaire(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    evaluatorClass = models.CharField(max_length=100, default="Evaluator")

    def __str__(self):
        return self.name

class Type(models.Model):
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Question(models.Model):
    question_questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questionQuestionnaire')
    question_type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='questionType')
    question_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='questionGroup')
    description = models.CharField(max_length=255)
    order = models.IntegerField(default=0)  # Order of the question in the questionnaire
    
    def __str__(self):
        return self.text

class Answer(models.Model):
    answer_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answerQuestion')
    order = models.IntegerField(default=0)  # Order of the answer in the question
    description = models.CharField(max_length=255)
    custom_answer = models.TextField(blank=True, null=True)  # Custom answer for open-ended questions
    
    def __str__(self):
        return self.text