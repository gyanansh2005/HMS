from rest_framework import viewsets
from .models import (
    CustomUser, StudentProfile, Hostel, Room,
    Allocation, RoomChangeRequest, FeePayment,
    ComplaintMaintenance, Feedback
)
from .serializers import (
    CustomUserSerializer, StudentProfileSerializer,
    HostelSerializer, RoomSerializer, AllocationSerializer,
    FeePaymentSerializer, ComplaintMaintenanceSerializer,
    FeedbackSerializer, RoomChangeRequestSerializer
)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer

class HostelViewSet(viewsets.ModelViewSet):
    queryset = Hostel.objects.all()
    serializer_class = HostelSerializer

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class AllocationViewSet(viewsets.ModelViewSet):
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer

class FeePaymentViewSet(viewsets.ModelViewSet):
    queryset = FeePayment.objects.all()
    serializer_class = FeePaymentSerializer

class ComplaintMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = ComplaintMaintenance.objects.all()
    serializer_class = ComplaintMaintenanceSerializer

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

class RoomChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = RoomChangeRequest.objects.all()
    serializer_class = RoomChangeRequestSerializer