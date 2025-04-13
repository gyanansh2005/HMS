from venv import logger
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from .forms import SignupForm, StaffSignupForm, ProfileUpdateForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, Hostel, Room, Allocation, StudentProfile, FeePayment, ComplaintMaintenance, Feedback
from app2.models import DiscussionMessage, Form, MessMenu, TodayMenu, MessRules
from app2.forms import MessMenuForm, MessRulesForm
from django.db.models import F, Count, Avg, Sum
from django.db import IntegrityError, transaction, models
from django.contrib.auth.decorators import login_required
import json
import time
from datetime import date
from random import randint

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
    
       
@login_required   
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
    student_profile = getattr(request.user, 'student_profile', None)
    allocation = request.user.allocations.first() if hasattr(request.user, 'allocations') else None
    profile_completion = calculate_profile_completion(request.user, student_profile)
    stats = {
        'bookings': request.user.allocations.count(),
        'complaints': request.user.complaintmaintenance_set.count(),  # Fixed
        'payments': request.user.payments.count(),
    }
    form = ProfileUpdateForm(instance=student_profile)
    
    return render(request, 'Rooms_profile.html', {
        'form': form,
        'student_profile': student_profile,
        'allocation': allocation,
        'profile_completion': profile_completion,
        'stats': stats,
    })
def calculate_profile_completion(user, profile):
    fields = [
        user.get_full_name(),
        profile.bio if profile else None,
        profile.contact_number if profile else None,
        profile.profile_picture if profile else None,
    ]
    filled = sum(1 for field in fields if field)
    return (filled / len(fields)) * 100

# views.py (edit_profile view)
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import ProfileUpdateForm
from .models import StudentProfile

@login_required
def edit_profile(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=student_profile
        )
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'contact_number': form.cleaned_data['contact_number'],
                    'bio': form.cleaned_data['bio']
                })
            messages.success(request, 'Your profile has been updated!')
            return redirect('profiles')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()  # Convert form errors to JSON
                }, status=400)
            # For non-AJAX POST, render the form with errors
            return render(request, 'Rooms_edit_profile.html', {'form': form})
    else:
        form = ProfileUpdateForm(instance=student_profile)
    
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from django.db.models import Count, F, Avg, Sum
from app2.models import Form
from .forms import EventForm  # Ensure this is imported
from datetime import date



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages  # Ensure this import is present
from django.db.models import Count, F, Avg, Sum
from .models import CustomUser, Room, ComplaintMaintenance, Feedback, Allocation, FeePayment
from app2.models import Form, DiscussionMessage, MessMenu, TodayMenu,ClaimRequest
from app2.forms import  DiscussionForm, MessMenuForm
from datetime import date

@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('index')
    
    active_tab = request.GET.get('tab', 'overview')
    
    # Common statistics
    total_users = CustomUser.objects.filter(is_staff=False).count()
    available_rooms = Room.objects.exclude(total_beds__lte=F('occupied_beds')).count()
    pending_requests = ComplaintMaintenance.objects.filter(status='pending').count()
    total_revenue = FeePayment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    avg_service_rating = Feedback.objects.aggregate(Avg('service_rating'))['service_rating__avg'] or 0
    allocation_stats = Allocation.objects.values('status').annotate(count=Count('status'))
    status_counts = {item['status']: item['count'] for item in allocation_stats}
    pending_allocations = next((item['count'] for item in allocation_stats if item['status'] == 'pending'), 0)
    confirmed_allocations = next((item['count'] for item in allocation_stats if item['status'] == 'confirmed'), 0)
    upcoming_events = Form.objects.filter(date__gte=date.today()).count()
    occupancy_rate = Room.objects.aggregate(total_beds=Sum('total_beds'), occupied=Sum('occupied_beds'))
    occupancy_percentage = (occupancy_rate['occupied'] / occupancy_rate['total_beds'] * 100) if occupancy_rate['total_beds'] else 0
    rating_progress_width = round((avg_service_rating / 5) * 100) if avg_service_rating else 0
    recent_complaints = ComplaintMaintenance.objects.order_by('-created_at')[:5]
    recent_payments = FeePayment.objects.order_by('-payment_date')[:5]

    context = {
        'active_tab': active_tab,
        'stats': {
            'total_users': total_users,
            'available_rooms': available_rooms,
            'pending_requests': pending_requests,
            'total_revenue': total_revenue,
            'avg_service_rating': round(avg_service_rating, 1),
            'pending_allocations': pending_allocations,
            'confirmed_allocations': confirmed_allocations,
            'upcoming_events': upcoming_events,
            'occupancy_percentage': round(occupancy_percentage, 1),
            'rating_progress_width': rating_progress_width,
        },
        'recent_complaints': recent_complaints,
        'recent_payments': recent_payments,
    }

    if active_tab == 'mess':
        search_query = request.GET.get('search', '')
        day_filter = request.GET.get('day', '').capitalize()
        menus = MessMenu.objects.all()
        today_menu = TodayMenu.objects.all()[:1]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        if search_query:
            menus = menus.filter(
                models.Q(menu__icontains=search_query) |
                models.Q(day__icontains=search_query) |
                models.Q(meal_type__icontains=search_query)
            )

        if day_filter:
            menus = menus.filter(day=day_filter)

        if not menus.exists() and day_filter:
            menus = MessMenu.objects.all()
            messages.info(request, f"No menus found for {day_filter}. Showing all menus.")

        if request.method == 'POST':
            form = MessMenuForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Menu item added successfully!')
                return redirect('/dashboard/?tab=mess')
            else:
                messages.error(request, 'Error adding menu item. Please check the form.')
        else:
            form = MessMenuForm()

        context.update({
            'day': days,
            'day_filter': day_filter,
            'menus': menus,
            'today_menu': today_menu,
            'search_query': search_query,
            'days': days,
            'form': form,
        })
    
    elif active_tab == 'users':
        search_query = request.GET.get('search', '')
        users = CustomUser.objects.filter(is_staff=False)
        if search_query:
            users = users.filter(email__icontains=search_query)
        context.update({'users': users, 'search_query': search_query})
        
    elif active_tab == 'requests':
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search', '')
        requests = ComplaintMaintenance.objects.all()
        if status_filter:
            requests = requests.filter(status=status_filter)
        if search_query:
            requests = requests.filter(details__icontains=search_query)
        context.update({'requests': requests, 'status_filter': status_filter, 'search_query': search_query})
        
    elif active_tab == 'allocations':
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search', '')
        allocations = Allocation.objects.select_related('room__hostel')
        if status_filter:
            allocations = allocations.filter(status=status_filter)
        if search_query:
            allocations = allocations.filter(room__room_number__icontains=search_query)
        context.update({'allocations': allocations, 'status_filter': status_filter, 'search_query': search_query})
    
    elif active_tab == 'events':
        events = Form.objects.all().order_by('date')
        context['events'] = events
    
    elif active_tab == 'add_event':
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Event added successfully!')
                return redirect('/dashboard/?tab=events')
            else:
                messages.error(request, 'Error adding event. Please check the form.')
        else:
            form = EventForm()
        context['form'] = form
        
    elif active_tab == 'notifications':
        message_id = request.GET.get('edit')
        delete_id = request.GET.get('delete')
        
        # Handle delete
        if delete_id and request.user.is_staff:
            try:
                DiscussionMessage.objects.get(id=delete_id).delete()
                messages.success(request, "Message deleted successfully")
                return redirect('/dashboard/?tab=notifications')
            except DiscussionMessage.DoesNotExist:
                messages.error(request, "Message not found")
                return redirect('/dashboard/?tab=notifications')
        
        # Handle POST for creating or editing messages
        if request.method == 'POST':
            if 'edit_id' in request.POST:
                try:
                    instance = DiscussionMessage.objects.get(id=request.POST['edit_id'])
                    form = DiscussionForm(request.POST, instance=instance, user=request.user)
                except DiscussionMessage.DoesNotExist:
                    messages.error(request, "Message not found")
                    return redirect('/dashboard/?tab=notifications')
            else:
                form = DiscussionForm(request.POST, user=request.user)
            
            if form.is_valid():
                obj = form.save(commit=False)
                if not obj.pk:  # Only set user for new messages
                    obj.user = request.user
                obj.save()
                messages.success(request, "Message saved successfully")
                return redirect('/dashboard/?tab=notifications')
            else:
                messages.error(request, "Error saving message")
        else:
            if message_id:
                try:
                    message = DiscussionMessage.objects.get(id=message_id)
                    form = DiscussionForm(instance=message, user=request.user)
                except DiscussionMessage.DoesNotExist:
                    messages.error(request, "Message not found")
                    form = DiscussionForm(user=request.user)
            else:
                form = DiscussionForm(user=request.user)
    
        chat_messages = DiscussionMessage.objects.all().order_by('-timestamp')[:50]
        context.update({
            'chat_messages': chat_messages,
            'discussion_form': form,
            'editing_message_id': message_id
        })
    elif active_tab == 'manage_claims':
        claims = ClaimRequest.objects.filter(is_approved=False)
        context.update({'claims': claims})

    return render(request, 'Rooms_dashboard.html', context)



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





@login_required
def update_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit events.")
        return redirect('index')
    
    event = get_object_or_404(Form, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('/dashboard/?tab=events')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'Rooms_admin_form.html', {'form': form, 'update': True})

@login_required
def delete_event(request, event_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete events.")
        return redirect('index')
    
    event = get_object_or_404(Form, id=event_id)
    event.delete()
    messages.success(request, 'Event deleted successfully!')
    return redirect('/dashboard/?tab=events')



from django.shortcuts import get_object_or_404
from app2.models import MessMenu, TodayMenu
from app2.forms import MessMenuForm

@login_required
def set_today_menu(request, menu_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to modify menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    TodayMenu.objects.create(
        day=menu.day,
        meal_type=menu.meal_type,
        menu=menu.menu
    )
    messages.success(request, f"{menu.meal_type} set as today's menu!")
    return redirect('/dashboard/?tab=mess')

@login_required
def update_mess_menu(request, menu_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to modify menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    if request.method == 'POST':
        form = MessMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu updated successfully!')
            return redirect('/dashboard/?tab=mess')
    else:
        form = MessMenuForm(instance=menu)
    
    return render(request, 'Rooms_admin_form.html', {'form': form, 'update': True})

@login_required
def delete_mess_menu(request, menu_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete menus.")
        return redirect('index')
    
    menu = get_object_or_404(MessMenu, id=menu_id)
    menu.delete()
    messages.success(request, 'Menu deleted successfully!')
    return redirect('/dashboard/?tab=mess')





def delete_notification(request, msg_id):
    message = get_object_or_404(DiscussionMessage, id=msg_id)
    if request.method == "POST":
        message.delete()
        messages.success(request, "Notification deleted successfully.")
        return redirect('dashboard')
    return render(request, 'confirm_delete_notification.html', {'message': message})



