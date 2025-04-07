from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import SignupForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Hostel, Room, Allocation
import json


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Replace 'home' with your redirect URL
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'Rooms_login.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')  # Replace 'home' with your redirect URL
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    return render(request, 'Rooms_signup.html', {'form': form})

def index(request):
    return render(request, 'Rooms_index.html',)


# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Hostel, Room, Allocation
import json

@require_GET
def get_floors(request, hostel_id):
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        return JsonResponse({'total_floors': hostel.total_floors})
    except Hostel.DoesNotExist:
        return JsonResponse({'error': 'Hostel not found'}, status=404)

@require_GET
def get_room_details(request):
    hostel_id = request.GET.get('hostel_id')
    floor = request.GET.get('floor')
    ac_type = request.GET.get('ac_type')
    room_id = request.GET.get('room_id')
    
    if room_id:
        try:
            room = Room.objects.get(id=room_id)
            return JsonResponse(room_to_json(room))
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
    
    rooms = Room.objects.filter(
        hostel_id=hostel_id,
        floor=floor,
        ac_type=ac_type
    )
    
    return JsonResponse({
        'rooms': [room_to_json(room) for room in rooms]
    })

def room_to_json(room):
    return {
        'id': room.id,
        'number': room.room_number,
        'type': room.room_type,
        'ac_type': room.ac_type,
        'beds_left': room.beds_left,
        'price': str(room.price),
        'amenities': room.amenities.split(',')
    }

@csrf_exempt
@require_POST
@transaction.atomic
def book_room(request):
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        room = Room.objects.select_for_update().get(id=room_id)
        
        if room.beds_left <= 0:
            return JsonResponse({'error': 'No beds available'}, status=400)
            
        # Create allocation
        Allocation.objects.create(
            user=user,
            room=room,
            status='pending'
        )
        
        # Update bed count atomically
        room.occupied_beds += 1
        room.save()
        
        return JsonResponse({
            'success': True,
            'redirect': '/profile/',
            'room': room_to_json(room)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




def room_allocation(request):
    return render(request, 'Rooms_room_allocation.html',)

def profile(request):
    return render(request, 'Rooms_profile.html',)
    return render(request, 'Rooms_profile.html',)