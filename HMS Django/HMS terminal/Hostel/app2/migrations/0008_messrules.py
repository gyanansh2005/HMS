# Generated by Django 5.2 on 2025-04-12 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app2', '0007_todaymenu'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessRules',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule', models.TextField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
