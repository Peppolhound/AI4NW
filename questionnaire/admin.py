from django.contrib import admin

# Register your models here.
from .models import Questionnaire, Group, Question, Answer, QuestionnaireValue, AnsweredQuestions

admin.site.register(Questionnaire)
admin.site.register(Group)
admin.site.register(Question)
admin.site.register(Answer)
@admin.register(QuestionnaireValue)
class QuestionnaireValueAdmin(admin.ModelAdmin):
    list_display = [field.name for field in QuestionnaireValue._meta.fields]
@admin.register(AnsweredQuestions)
class AnsweredQuestionsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AnsweredQuestions._meta.fields]