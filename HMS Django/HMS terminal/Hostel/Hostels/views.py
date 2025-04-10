from venv import logger
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from .forms import SignupForm, StaffSignupForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, Hostel, Room, Allocation, StudentProfile
import json
from django.db.models import F
from django.db import IntegrityError, transaction
from .models import Hostel, Room, Allocation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileUpdateForm
import time
from datetime import datetime
from random import randint 
from .models import FeePayment
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from django.db.models import Count, Avg


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)  # Use 'username' if email is the username field
        if user is not None:
            login(request, user)
            role = request.GET.get('role', '')  # Retrieve 'role' from query parameters
            if role == 'staff' and not (user.is_staff or user.is_superuser):
                messages.error(request, "Staff access requires authorized credentials")
                return redirect('login?role=staff')
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            else:
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
                student_profile = user.student_profile  # Get the auto-created profile
                student_profile.contact_number = form.cleaned_data['contact_number']
                student_profile.save()
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
        allocation = Allocation.objects.create(
            user=user,
            room=room,
            status='pending'
        )
        
        # Update bed count atomically
        room.occupied_beds += 1
        room.save()
        
        return JsonResponse({
            'success': True,
            'redirect': reverse('post_allocation'),
            'room': room_to_json(room),
            'allocation_id': allocation.id  # Fixed: Use the created allocation instance
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@transaction.atomic
def room_allocation(request):
    # Handle POST request for room allocation
    if request.method == 'POST':
        if request.user.allocations.filter(status__in=['pending', 'confirmed']).exists():
            messages.error(request, "You already have an active room allocation!")
            return redirect('room_allocation')
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
                return redirect('profiles')

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
        rooms = Room.objects.all().annotate(
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

        print(f"Returning rooms: {room_data}")  # Debug print
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


def profiles(request):
    # Get the latest allocation for the user
    student_profile = None
    if not request.user.is_staff and not request.user.is_superuser:
        student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    allocation = request.user.allocations.select_related('room__hostel').last()
    form = ProfileUpdateForm(instance=student_profile) if student_profile else None
    
    return render(request, 'Rooms_profile.html', {
        'form': form,
        'allocation': allocation,
        'student_profile': student_profile
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
            return redirect('profiles')  # Ensure 'profiles' URL is mapped to Rooms_profile.html in your URLs configuration
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


# Add these imports
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import FeePayment
from .forms import PaymentForm  # We'll create this next

from django.views.decorators.csrf import csrf_exempt


from .forms import CardPaymentForm  # Ensure this is imported

# In views.py
import socket
from django.db import connections

from django.db import transaction, DatabaseError
import time
import logging

logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def payment_page(request):
    try:
        # Verify allocation exists
        allocation = request.user.allocations.select_related('room').latest('allocation_date')
        amount_due = allocation.room.price * 6

        if request.method == 'POST':
            form = CardPaymentForm(request.POST)
            if not form.is_valid():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid card details',
                    'errors': form.errors.as_json()
                }, status=400)

            # Simulate payment gateway delay
            time.sleep(2)  # Simulate network delay (remove in production)

            # Generate unique transaction ID
            transaction_id = None
            for _ in range(5):
                transaction_id = f"TXN{int(time.time())}{randint(1000, 9999)}"
                if not FeePayment.objects.filter(transaction_id=transaction_id).exists():
                    break

            # Simulate payment success/failure (for demo purposes)
            card_number = form.cleaned_data['card_number']
            if card_number.endswith('0000'):  # Simulate failure for specific card numbers
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment declined by bank'
                }, status=400)

            # Create payment record
            try:
                with transaction.atomic():
                    payment = FeePayment.objects.create(
                        user=request.user,
                        allocation=allocation,
                        amount=amount_due,
                        transaction_id=transaction_id,
                        status='completed'
                        )
                    allocation.status = 'confirmed'
                    allocation.save()
            except IntegrityError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Duplicate transaction detected'
                }, status=409)

            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('payment_success', kwargs={'transaction_id': transaction_id})
            })

        return render(request, 'Rooms_payment_page.html', {
            'amount_due': amount_due,
            'allocation': allocation,
            'form': CardPaymentForm()
        })

    except Allocation.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'No room allocation found. Book a room first.'
        }, status=400)
    except Exception as e:
        logger.error(f"Payment System Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Payment system temporarily unavailable'
        }, status=500)       
        
@login_required
def payment_success(request, transaction_id):
    payment = get_object_or_404(FeePayment, transaction_id=transaction_id)
    auth_code = f"SIM{randint(100000, 999999)}"
    return render(request, 'Rooms_payment_success.html', {
        'payment': payment,
        'virtual_account': f"VA{randint(10000000, 99999999)}",
        'payment_gateway': "SecurePay Simulation",
        'auth_code': auth_code,  # Add this
    })
    
@login_required
def post_allocation(request):
    # Get the latest allocation for the user
    allocation = request.user.allocations.latest('allocation_date')
    return render(request, 'Rooms_post_allocation.html', {
        'allocation': allocation,
    })
    
    
# views.py
from .models import ComplaintMaintenance, Feedback
from .forms import ComplaintMaintenanceForm, FeedbackForm

@login_required
def complaint_maintenance(request):
    if request.method == 'POST':
        form = ComplaintMaintenanceForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            messages.success(request, 'Your request has been submitted!')
            return redirect('complaint_maintenance')
    else:
        form = ComplaintMaintenanceForm()
    
    requests = ComplaintMaintenance.objects.filter(user=request.user)
    return render(request, 'Rooms_complaint_and_maintenance.html', {
        'form': form,
        'requests': requests
    })

@login_required
def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback')
    else:
        form = FeedbackForm()
    
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'Rooms_feedback.html', {
        'form': form,
        'feedbacks': feedbacks
    })

def terms_conditions(request):
    return render(request, 'Rooms_terms_and_conditions.html')


# views.py
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from django.db.models import Count, F, Avg, Sum
from django.contrib.auth import logout

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from django.db.models import Count, F, Avg, Sum

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from django.db.models import Count, F, Avg, Sum

@login_required
def dashboard(request):
    # Restrict access to staff only
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('index')
    
    # Get active tab from GET parameter
    active_tab = request.GET.get('tab', 'overview')
    
    # Calculate dynamic statistics
    total_users = CustomUser.objects.filter(is_staff=False).count()  # Exclude staff/superusers
    available_rooms = Room.objects.exclude(total_beds__lte=F('occupied_beds')).count()  # Rooms with available beds
    pending_requests = ComplaintMaintenance.objects.filter(status='pending').count()
    total_feedback = Feedback.objects.count()
    avg_service_rating = Feedback.objects.aggregate(Avg('service_rating'))['service_rating__avg'] or 0
    total_revenue = FeePayment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate allocation statistics
    allocation_stats = Allocation.objects.values('status').annotate(count=Count('status'))
    pending_allocations = next((item['count'] for item in allocation_stats if item['status'] == 'pending'), 0)
    confirmed_allocations = next((item['count'] for item in allocation_stats if item['status'] == 'confirmed'), 0)
    
    # Calculate progress bar width for rating (0-100% based on 5 stars)
    rating_progress_width = round((avg_service_rating / 5) * 100) if avg_service_rating else 0
    
    # Additional stats for better insights
    occupied_rooms = Room.objects.filter(occupied_beds__gte=F('total_beds')).count()
    recent_allocations = Allocation.objects.select_related('room__hostel').order_by('-allocation_date')[:5]
    pending_payments = FeePayment.objects.filter(status='pending').count()
    recent_complaints = ComplaintMaintenance.objects.order_by('-created_at')[:5]
    recent_payments = FeePayment.objects.order_by('-payment_date')[:5]

    context = {
        'active_tab': active_tab,
        'stats': {
            'total_users': total_users,
            'available_rooms': available_rooms,
            'pending_requests': pending_requests,
            'total_feedback': total_feedback,
            'avg_service_rating': round(avg_service_rating, 1),
            'total_revenue': total_revenue,
            'pending_allocations': pending_allocations,
            'confirmed_allocations': confirmed_allocations,
            'occupied_rooms': occupied_rooms,
            'pending_payments': pending_payments,
            'rating_progress_width': rating_progress_width,  # Added calculated width
        },
        'recent_allocations': recent_allocations,
        'recent_complaints': recent_complaints,
        'recent_payments': recent_payments,
    }
    
    # Handle users tab
    if active_tab == 'users':
        search_query = request.GET.get('search', '')
        users = CustomUser.objects.filter(is_staff=False)
        if search_query:
            users = users.filter(email__icontains=search_query)
        context.update({'users': users, 'search_query': search_query})

    return render(request, 'Rooms_dashboard.html', context)
# views.py




def about(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'Rooms_about.html', {'feedbacks': feedbacks})



def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('index')  # Replace 'index' with the name of your homepage URL pattern




#! admin



@login_required
def view_requests(request):
    # Implement requests view
    return render(request, 'Rooms_dashboard.html', {'active_tab': 'requests'})

@login_required
def view_allocations(request):
    # Implement allocations view
    return render(request, 'Rooms_dashboard.html', {'active_tab': 'allocations'})

@login_required
def edit_user(request, user_id):
    # Implement user editing
    return redirect('admin_dashboard')

@login_required
def delete_user(request, user_id):
    # Implement user deletion
    return redirect('admin_dashboard')


@login_required
def staff_signup_view(request):
    # Restrict access to staff users only
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('index')

    if request.method == 'POST':
        form = StaffSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff account created successfully!")
            return redirect('admin_dashboard')
    else:
        form = StaffSignupForm()

    return render(request, 'Rooms_staff_signup.html', {'form': form})




@login_required
def user_management(request):
    """Handle user management tab"""
    if not request.user.is_staff:
        return redirect('index')
    
    search_query = request.GET.get('search', '')
    users = CustomUser.objects.filter(is_staff=False)  # Only non-staff users
    if search_query:
        users = users.filter(email__icontains=search_query)

    return render(request, 'Rooms_dashboard.html', {
        'active_tab': 'users',
        'users': users,
        'search_query': search_query,
        'users_count': users.count()
    })

@login_required
def view_requests(request):
    """Handle requests tab"""
    if not request.user.is_staff:
        return redirect('index')
    
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    requests = ComplaintMaintenance.objects.all()
    if status_filter:
        requests = requests.filter(status=status_filter)
    if search_query:
        requests = requests.filter(details__icontains=search_query)

    return render(request, 'Rooms_dashboard.html', {
        'active_tab': 'requests',
        'requests': requests,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
def view_allocations(request):
    """Handle allocations tab"""
    if not request.user.is_staff:
        return redirect('index')
    
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    allocations = Allocation.objects.select_related('room__hostel')
    if status_filter:
        allocations = allocations.filter(status=status_filter)
    if search_query:
        allocations = allocations.filter(room__room_number__icontains=search_query)

    return render(request, 'Rooms_dashboard.html', {
        'active_tab': 'allocations',
        'allocations': allocations,
        'status_filter': status_filter,
        'search_query': search_query
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import CustomUser

@login_required
def view_users(request):
    if not request.user.is_staff:
        return redirect('index')  # Redirect non-staff users
    
    search_query = request.GET.get('search', '')
    users = CustomUser.objects.filter(is_staff=False)
    if search_query:
        users = users.filter(email__icontains=search_query)  # Simple search by email
    
    context = {
        'active_tab': 'users',
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'Rooms_dashboard.html', context)




