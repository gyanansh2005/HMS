# Generated by Django 5.2 on 2025-04-10 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app2', '0003_remove_form_description_alter_form_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='description',
            field=models.TextField(blank=True, help_text='Event description', null=True),
        ),
    ]
