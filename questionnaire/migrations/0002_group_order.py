# Generated by Django 5.2 on 2025-05-13 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
