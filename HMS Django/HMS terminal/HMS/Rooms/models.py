from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Hostel(models.Model):
    name = models.CharField(max_length=100)
    campus = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='hostels/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.campus})"

class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single Seater'),
        ('double', 'Double Sharing'),
        ('four', '4 Sharing'),
    ]
    
    AC_TYPES = [
        ('ac', 'AC'),
        ('non_ac', 'Non-AC'),
    ]
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    floor = models.IntegerField()
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    ac_type = models.CharField(max_length=6, choices=AC_TYPES, default='non_ac')
    capacity = models.IntegerField()
    beds_occupied = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField(blank=True)
    
    @property
    def beds_left(self):
        return self.capacity - self.beds_occupied
    
    def __str__(self):
        return f"{self.hostel.name} - Floor {self.floor} - Room {self.room_number} ({self.get_room_type_display()})"

    class Meta:
        unique_together = ('hostel', 'floor', 'room_number')
        ordering = ['hostel', 'floor', 'room_number']

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='occupants')
    allocated_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"
@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created:
        Student.objects.create(user=instance)



class Allocation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('booked', 'Booked'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    allocation_date = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_allocations')
    
    class Meta:
        unique_together = ('student', 'room')
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.student} - {self.room} ({self.status})"

class AvailableRoom(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, primary_key=True, related_name='availability')
    is_available = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room} - {'Available' if self.is_available else 'Booked'}"

class BookedRoom(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    checkout_date = models.DateTimeField(null=True, blank=True)
    payment_status = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ('room', 'student')
        ordering = ['-booking_date']
    
    def __str__(self):
        return f"{self.room} booked by {self.student}"

class MaintenanceRequest(models.Model):
    REQUEST_TYPES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('furniture', 'Furniture'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='maintenance_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenance_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    
    def __str__(self):
        return f"{self.get_request_type_display()} request for {self.room} ({self.status})"

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='feedbacks')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Feedback from {self.student} for {self.hostel}"



# Signal to update available room status when allocation changes
@receiver(post_save, sender=Allocation)
def update_room_availability(sender, instance, **kwargs):
    room = instance.room
    available_room, created = AvailableRoom.objects.get_or_create(room=room)
    available_room.is_available = room.beds_left > 0
    available_room.save()