# Generated by Django 5.2 on 2025-06-05 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0014_remove_answeredquestions_uploaded_file_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answeredquestions',
            name='uploaded_files',
        ),
        migrations.AddField(
            model_name='answeredquestions',
            name='uploaded_file',
            field=models.FileField(blank=True, null=True, upload_to='media/'),
        ),
    ]
