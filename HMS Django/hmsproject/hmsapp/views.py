from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, 'index.html')

def room_allocation(request):
    return render(request, 'room_allocation.html')

def complaint_and_maintenance(request):
    return render(request, 'complaint_and_maintenance.html')

def hostel_details(request):
    return render(request, 'hostel_details.html')

def feedback(request):
    return render(request, 'feedback.html')

def about(request):
    return render(request, 'about.html')

def profile(request):
    return render(request, 'profile.html')

def payment(request):
    return render(request, 'payment.html')

def feedback(request):
    return render(request, 'feedback.html')