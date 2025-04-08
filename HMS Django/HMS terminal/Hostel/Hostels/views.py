from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import SignupForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Hostel, Room, Allocation, StudentProfile
import json
from django.db.models import F
from django.db import transaction
from .models import Hostel, Room, Allocation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileUpdateForm 


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)  # Use 'username' if email is the username field
        if user is not None:
            login(request, user)
            return redirect('index')  # Replace 'home' with your redirect URL
        else:
            print(f"Authentication failed for {email}")
            messages.error(request, 'Invalid email or password.')
    return render(request, 'Rooms_login.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            if not user.is_staff and not user.is_superuser:
                StudentProfile.objects.get_or_create(user=user, contact_number=form.cleaned_data['contact_number'])
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
            'room': room_to_json(room),
            'allocation_id': Allocation.id  # Add allocation ID
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



def room_allocation(request):
    # Handle POST request for room allocation
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data with proper validation
                hostel_id = request.POST.get('hostel')
                room_number = request.POST.get('room_number')
                student_name = request.POST.get('student_name')
                student_roll_no = request.POST.get('student_roll_no')

                if not all([hostel_id, room_number, student_name, student_roll_no]):
                    messages.error(request, "All fields are required")
                    return redirect('room_allocation')

                # Get the specific room with hostel context
                room = Room.objects.select_for_update().get(
                    hostel_id=hostel_id,
                    room_number=room_number
                )

                # Check bed availability
                if room.beds_left <= 0:
                    messages.error(request, "No beds available in this room")
                    return redirect('room_allocation')

                # Create allocation
                Allocation.objects.create(
                    user=request.user,
                    room=room,
                    status='pending'
                )

                # Update bed count atomically
                room.occupied_beds = F('occupied_beds') + 1
                room.save(update_fields=['occupied_beds'])

                messages.success(request, 
                    f"Room {room_number} allocated successfully for {student_name}!"
                )
                return redirect('profile')

        except Room.DoesNotExist:
            messages.error(request, "Invalid room selection")
        except Room.MultipleObjectsReturned:
            messages.error(request, "Database error: Duplicate rooms detected")
        except Exception as e:
            messages.error(request, f"Allocation failed: {str(e)}")

        return redirect('room_allocation')

    # Handle GET request for showing available rooms
    hostels = Hostel.objects.all()
    selected_hostel = request.GET.get('hostel')
    selected_floor = request.GET.get('floor')
    selected_ac_type = request.GET.get('ac_type')

    # Base query with available beds
    rooms = Room.objects.annotate(
        available_beds=F('total_beds') - F('occupied_beds')
    ).filter(available_beds__gt=0)

    # Apply filters
    if selected_hostel:
        rooms = rooms.filter(hostel_id=selected_hostel)
    if selected_floor:
        rooms = rooms.filter(floor=selected_floor)
    if selected_ac_type:
        rooms = rooms.filter(ac_type=selected_ac_type)

    # Categorize rooms
    room_types = {
        'four': '4-Sharing',
        'double': 'Double Sharing',
        'single': 'Single Seater'
    }

    categorized_rooms = {
        rt: {
            'available': rooms.filter(room_type=rt),
            'booked': Room.objects.filter(
                room_type=rt,
                total_beds=F('occupied_beds')
            )
        } for rt in room_types
    }

    return render(request, 'Rooms_room_allocation.html', {
        'hostels': hostels,
        'selected_hostel': selected_hostel,
        'selected_floor': selected_floor,
        'selected_ac_type': selected_ac_type,
        'categorized_rooms': categorized_rooms,
        'room_types': room_types
    })
@require_GET
def get_available_rooms(request):
    try:
        rooms = Room.objects.annotate(
            available_beds=F('total_beds') - F('occupied_beds')
        )
        
        # Apply filters
        hostel_id = request.GET.get('hostel')
        floor = request.GET.get('floor')
        ac_type = request.GET.get('ac_type')

        if hostel_id:
            rooms = rooms.filter(hostel_id=hostel_id)
        if floor:
            rooms = rooms.filter(floor=floor)
        if ac_type:
            rooms = rooms.filter(ac_type=ac_type)

        room_data = [{
            'id': room.id,
            'number': room.room_number,
            'type': room.room_type,
            'ac_type': room.ac_type,
            'beds_left': room.available_beds,
            'price': str(room.price)
        } for room in rooms]

        return JsonResponse({'rooms': room_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    
    
@require_GET
def get_floors(request, hostel_id):
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        floors = [str(i+1) for i in range(hostel.total_floors)]
        return JsonResponse({'floors': floors})
    except Hostel.DoesNotExist:
        return JsonResponse({'error': 'Hostel not found'}, status=404)


def profile(request):
    # Get the latest allocation for the user
    allocation = request.user.allocations.select_related('room__hostel').last()
    form = ProfileUpdateForm(instance=request.user.student_profile)
    return render(request, 'Rooms_profile.html', {
        'form': form,
        'allocation': allocation  # Add this line
    })

# views.py (edit_profile view)
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.student_profile
        )
        if form.is_valid():
            form.save()
            # Handle AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'contact_number': form.cleaned_data['contact_number'],
                    'bio': form.cleaned_data['bio']
                })
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ProfileUpdateForm(instance=request.user.student_profile)
    
    return render(request, 'Rooms_edit_profile.html', {'form': form})

# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt
def update_profile_pic(request):
    if request.method == 'POST':
        try:
            profile = request.user.student_profile
            profile.profile_picture = request.FILES.get('profile_picture')
            profile.save()
            return JsonResponse({
                'success': True,
                'new_url': profile.profile_picture.url
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



def hostel_details(request):
    hostels = Hostel.objects.all()
    return render(request, 'Rooms_hostel_details.html', {'hostels': hostels})
