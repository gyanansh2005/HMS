from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import Hostel, Room, Student, Allocation, AvailableRoom, BookedRoom
from .forms import UserEditForm, ProfileEditForm, CustomUserCreationForm

def index(request):
    return render(request, 'Rooms_index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            
            # Check if user has a room allocation
            try:
                student = user.student_profile
                if Allocation.objects.filter(student=student, status='booked').exists():
                    return redirect('profile')
            except Student.DoesNotExist:
                pass
                
            if user.is_staff or user.groups.filter(name='admin').exists():
                return redirect('admin_dashboard')
            return redirect('room_allocation')
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'Rooms_login.html')

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('index')

# In views.py, modify the signup view
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Safely get or create Student profile
                student, created = Student.objects.get_or_create(
                    user=user,
                    defaults={'roll_number': form.cleaned_data['roll_number']}
                )
                
                if not created:
                    student.roll_number = form.cleaned_data['roll_number']
                    student.save()
                
                auth_login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('room_allocation')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'Rooms_signup.html', {'form': form})


def room_allocation(request):
    context = {
        'hostels': Hostel.objects.all(),
        'selected_hostel': None,
        'selected_floor': None,
        'selected_ac_type': None,
        'selected_room_number': None,
        'selected_room_type': None,
        'selected_room_display': None,
        'four_sharing_available': [],
        'double_sharing_available': [],
        'single_seater_available': [],
        'four_sharing_booked': [],
        'double_sharing_booked': [],
        'single_seater_booked': [],
    }

    if request.method == 'GET':
        context['selected_hostel'] = request.GET.get('hostel')
        context['selected_floor'] = request.GET.get('floor')
        context['selected_ac_type'] = request.GET.get('ac_type')
        context['selected_room_number'] = request.GET.get('room_number')
        context['selected_room_type'] = request.GET.get('room_type')

        if context['selected_room_number'] and context['selected_room_type']:
            try:
                room = Room.objects.get(
                    hostel_id=context['selected_hostel'],
                    floor=context['selected_floor'],
                    room_number=context['selected_room_number'],
                    room_type=context['selected_room_type']
                )
                context['selected_room_display'] = f"Room {room.room_number} ({room.get_room_type_display()})"
            except Room.DoesNotExist:
                messages.error(request, 'Selected room not found')

        if context['selected_hostel'] and context['selected_floor']:
            rooms = Room.objects.filter(
                hostel_id=context['selected_hostel'],
                floor=context['selected_floor']
            )
            if context['selected_ac_type']:
                rooms = rooms.filter(ac_type=context['selected_ac_type'])

            for room in rooms:
                room_data = {
                    'number': room.room_number,
                    'beds_left': room.beds_left,
                    'ac_type': room.get_ac_type_display(),
                }
                
                if room.beds_left <= 0:
                    if room.room_type == 'four':
                        context['four_sharing_booked'].append(room_data)
                    elif room.room_type == 'double':
                        context['double_sharing_booked'].append(room_data)
                    elif room.room_type == 'single':
                        context['single_seater_booked'].append(room_data)
                else:
                    if room.room_type == 'four':
                        context['four_sharing_available'].append(room_data)
                    elif room.room_type == 'double':
                        context['double_sharing_available'].append(room_data)
                    elif room.room_type == 'single':
                        context['single_seater_available'].append(room_data)

    if request.method == 'POST':
        hostel_id = request.POST.get('hostel')
        floor = request.POST.get('floor')
        room_number = request.POST.get('room_number')
        room_type = request.POST.get('room_type')
        student_name = request.POST.get('student_name')
        roll_number = request.POST.get('student_roll_no')
        
        try:
            room = Room.objects.get(
                hostel_id=hostel_id,
                floor=floor,
                room_number=room_number,
                room_type=room_type
            )
            
            if room.beds_left <= 0:
                messages.error(request, 'No available beds in this room.')
                return redirect('room_allocation')
            
            # Get or update student profile
            student = request.user.student_profile
            if roll_number:
                student.roll_number = roll_number
                student.save()
            
            if student_name:
                request.user.first_name, *last_name = student_name.split(' ', 1)
                request.user.last_name = last_name[0] if last_name else ''
                request.user.save()
            
            # Check for existing allocation
            if Allocation.objects.filter(student=student, status='booked').exists():
                messages.error(request, 'You already have a room allocated.')
                return redirect('profile')
            
            # Create allocation
            allocation = Allocation.objects.create(
                student=student,
                room=room,
                status='booked'
            )
            
            # Update room occupancy
            room.beds_occupied += 1
            room.save()
            
            # Create booking record
            BookedRoom.objects.create(student=student, room=room)
            
            # Update student's room reference
            student.room = room
            student.save()
            
            # Update availability
            available_room, _ = AvailableRoom.objects.get_or_create(room=room)
            available_room.is_available = room.beds_left > 0
            available_room.save()
            
            messages.success(request, 'Room booked successfully!')
            return redirect('payment')
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'Rooms_room_allocation.html', context)

@require_GET
def get_available_rooms(request):
    hostel_id = request.GET.get('hostel')
    floor = request.GET.get('floor')
    ac_type = request.GET.get('ac_type', None)
    
    if not hostel_id or not floor:
        return JsonResponse({'error': 'Hostel and floor are required'}, status=400)
    
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        rooms = Room.objects.filter(hostel=hostel, floor=floor)
        if ac_type:
            rooms = rooms.filter(ac_type=ac_type)
        
        available_rooms = {'four': [], 'double': [], 'single': []}
        booked_rooms = {'four': [], 'double': [], 'single': []}
        
        for room in rooms:
            room_data = {
                'number': room.room_number,
                'beds_left': room.beds_left,
                'ac_type': room.ac_type,
            }
            
            if room.beds_left <= 0:
                booked_rooms[room.room_type].append(room_data)
            else:
                available_rooms[room.room_type].append(room_data)
        
        return JsonResponse({
            'available': available_rooms,
            'booked': booked_rooms,
        })
    except Hostel.DoesNotExist:
        return JsonResponse({'error': 'Hostel not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def payment(request):
    # Get the student's latest booking
    booking = BookedRoom.objects.filter(student=request.user.student_profile).last()
    context = {'booking': booking}
    return render(request, 'Rooms_payment.html', context)

# Add to complaint_and_maintenance view
@login_required
def complaint_and_maintenance(request):
    if request.method == 'POST':
        try:
            student = request.user.student_profile
            room = student.room
            request_type = request.POST.get('request_type')
            description = request.POST.get('description')
            
            MaintenanceRequest.objects.create(
                student=student,
                room=room,
                request_type=request_type,
                description=description
            )
            messages.success(request, 'Your maintenance request has been submitted!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
    
    return render(request, 'Rooms_complaint_and_maintenance.html')

# Add to feedback view
@login_required
def feedback(request):
    if request.method == 'POST':
        try:
            student = request.user.student_profile
            hostel_id = request.POST.get('hostel_id')
            rating = request.POST.get('rating')
            comments = request.POST.get('comments')
            is_anonymous = 'is_anonymous' in request.POST
            
            Feedback.objects.create(
                student=student,
                hostel_id=hostel_id,
                rating=rating,
                comments=comments,
                is_anonymous=is_anonymous
            )
            messages.success(request, 'Thank you for your feedback!')
            return redirect('hostel_details')
        except Exception as e:
            messages.error(request, f'Error submitting feedback: {str(e)}')
    
    hostels = Hostel.objects.all()
    return render(request, 'Rooms_feedback.html', {'hostels': hostels})


def hostel_details(request):
    hostels = Hostel.objects.all()
    return render(request, 'Rooms_hostel_details.html', {'hostels': hostels})


def about(request):
    return render(request, 'Rooms_about.html')

@login_required
def profile(request):
    student = request.user.student_profile
    allocation = Allocation.objects.filter(student=student).first()
    booking = BookedRoom.objects.filter(student=student).first()
    
    context = {
        'student': student,
        'allocation': allocation,
        'booking': booking
    }
    return render(request, 'Rooms_profile.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.groups.filter(name='admin').exists())
def admin_dashboard(request):
    users_count = User.objects.count()
    rooms_count = Room.objects.count()
    available_rooms = AvailableRoom.objects.filter(is_available=True).count()
    pending_allocations = Allocation.objects.filter(status='pending').count()
    bookings = BookedRoom.objects.select_related('student', 'room').all()[:10]
    
    context = {
        'users_count': users_count,
        'rooms_count': rooms_count,
        'available_rooms': available_rooms,
        'pending_allocations': pending_allocations,
        'recent_bookings': bookings
    }
    return render(request, 'Rooms_admin_dashboard.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.student_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.student_profile)
    
    return render(request, 'Rooms_edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'Rooms_change_password.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.student_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.student_profile)
    
    return render(request, 'Rooms_edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })