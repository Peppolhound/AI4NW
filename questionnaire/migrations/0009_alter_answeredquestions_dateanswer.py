# Generated by Django 4.2.11 on 2025-05-22 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0008_alter_answeredquestions_uploaded_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answeredquestions',
            name='dateAnswer',
            field=models.DateField(auto_now_add=True),
        ),
    ]
