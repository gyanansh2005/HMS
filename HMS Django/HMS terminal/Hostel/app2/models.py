from django.db import models

class Form(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=255)
    description = models.TextField(help_text="Event description", blank=True, null=True)
    organizer = models.CharField(max_length=255)
    description = models.TextField(help_text="Event description", blank=True, null=True)  # Note: 'description' is defined twice, fix this if intentional

    def __str__(self):
        return self.name

class MessMenu(models.Model):
    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]
    MEAL_TYPE_CHOICES = [
        ("Breakfast", "Breakfast"),
        ("Lunch", "Lunch"),
        ("Dinner", "Dinner"),
    ]
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    menu = models.TextField()

    class Meta:
        unique_together = ['day', 'meal_type']  # Ensures no duplicate meal types per day

    def __str__(self):
        return f"{self.day} - {self.meal_type}"

class TodayMenu(models.Model):
    day = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=20)
    menu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.day} - {self.meal_type}"

class MessRules(models.Model):
    rule = models.TextField()
    order = models.PositiveIntegerField(default=0)  # For sorting rules
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.rule[:50]

    class Meta:
        ordering = ['order']
        
        
# Add to app2/models.py
class DiscussionMessage(models.Model):
    user = models.ForeignKey('Hostels.CustomUser', on_delete=models.CASCADE)  # Adjust 'main' to your app name
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_notification = models.BooleanField(default=False)  # For system notifications

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email}: {self.message[:30]}"