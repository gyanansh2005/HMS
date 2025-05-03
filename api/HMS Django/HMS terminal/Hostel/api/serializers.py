from rest_framework import serializers
from .models import (
    CustomUser, StudentProfile, Hostel, Room,
    Allocation, RoomChangeRequest, FeePayment,
    ComplaintMaintenance, Feedback
)

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'roll_number', 'is_staff']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = '__all__'

class HostelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hostel
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    hostel = HostelSerializer()
    
    class Meta:
        model = Room
        fields = '__all__'

class AllocationSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    room = RoomSerializer()
    
    class Meta:
        model = Allocation
        fields = '__all__'

class FeePaymentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    allocation = AllocationSerializer()
    
    class Meta:
        model = FeePayment
        fields = '__all__'

class ComplaintMaintenanceSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    
    class Meta:
        model = ComplaintMaintenance
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    
    class Meta:
        model = Feedback
        fields = '__all__'

class RoomChangeRequestSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    current_allocation = AllocationSerializer()
    requested_room = RoomSerializer()
    
    class Meta:
        model = RoomChangeRequest
        fields = '__all__'