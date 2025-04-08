from django.contrib.auth.models import AbstractUser
# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('roll_number', 'ADMIN')  # Optional default
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    roll_number = models.CharField(max_length=20, blank=True, null=True)  # Optional field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # roll_number is optional

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    contact_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

class Hostel(models.Model):
    name = models.CharField(max_length=100)
    total_floors = models.PositiveIntegerField()
    main_image = models.ImageField(upload_to='hostels/')
    features = models.TextField(help_text="Comma-separated list of features")
    
    def feature_list(self):
        return [f.strip() for f in self.features.split(',')]

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPES = (
        ('four', '4-Sharing'),
        ('double', 'Double Sharing'),
        ('single', 'Single Seater')
    )
    AC_TYPES = (
        ('ac', 'AC'),
        ('non_ac', 'Non-AC'),
    )
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    floor = models.PositiveIntegerField()
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    ac_type = models.CharField(max_length=10, choices=AC_TYPES)
    total_beds = models.PositiveIntegerField()
    occupied_beds = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField()

    @property
    def beds_left(self):
        return self.total_beds - self.occupied_beds

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hostel', 'room_number'],
                name='unique_room_per_hostel'
            )
        ]

class Allocation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    allocation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.email} - {self.room.room_number}"