# Generated by Django 5.2 on 2025-04-09 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='organizer',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
