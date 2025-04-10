from django.db import models

# Create your models here.





class Form(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)
    description = models.TextField(help_text="Event description", blank=True, null=True)


    def __str__(self):
        return self.name