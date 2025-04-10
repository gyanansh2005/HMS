from django.db import models

# Create your models here.

class Form(models.Model):
    name = models.CharField(max_length=100, help_text="Event name")
    date = models.CharField(help_text="Event date")
    time = models.CharField(help_text="Event time")
    venue = models.CharField(max_length=200, help_text="Event venue")
    description = models.TextField(help_text="Event description", blank=True, null=True)
    organizer = models.CharField(max_length=100, blank=True, null=True)  # Make sure this line exists


    def __str__(self):
        return self.name

from django.db import models

class Form(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)

    def __str__(self):
        return self.name