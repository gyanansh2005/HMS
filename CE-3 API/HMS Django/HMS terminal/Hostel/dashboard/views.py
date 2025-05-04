import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

FLASK_API = 'http://localhost:5000/api'

def is_admin(user):
    return user.is_authenticated and user.is_staff

def safe_json(url):
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', ''):
            return resp.json()
        else:
            print(f"Error loading data from {url}: Status {resp.status_code}")
            print(f"Response: {resp.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching {url}: {str(e)}")
        return []

def dashboard_home(request):
    room_allocations = safe_json(f'{FLASK_API}/room_allocations')
    users = safe_json(f'{FLASK_API}/users')
    feedbacks = safe_json(f'{FLASK_API}/feedbacks')
    requests_list = safe_json(f'{FLASK_API}/requests')
    return render(request, 'home.html', {
        'room_allocations': room_allocations,
        'users': users,
        'feedbacks': feedbacks,
        'requests_list': requests_list,
        'user': request.user,
        'section': 'home'
    })

# ------------------ ROOM ALLOCATIONS ------------------
def room_allocations(request):
    try:
        data = safe_json(f'{FLASK_API}/room_allocations')
        if not data:
            messages.warning(request, 'No room allocations found or error fetching data')
        return render(request, 'room_allocations.html', {
            'allocations': data,
            'section': 'allocations',
            'user': request.user
        })
    except Exception as e:
        messages.error(request, f'Error loading room allocations: {str(e)}')
        return render(request, 'room_allocations.html', {
            'allocations': [],
            'section': 'allocations',
            'user': request.user
        })

def add_room_allocation(request):
    if request.method == 'POST':
        payload = {
            'hostel': request.POST['hostel'],
            'floor': request.POST['floor'],
            'room_number': request.POST['room_number'],
            'room_type': request.POST['room_type'],
            'beds_left': request.POST.get('beds_left', 4),
            'user_id': request.POST['user_id'],
            'student_name': request.POST['student_name'],
            'student_roll_no': request.POST['student_roll_no'],
        }
        resp = requests.post(f'{FLASK_API}/room_allocations', json=payload)
        if resp.status_code == 201:
            messages.success(request, 'Room Allocation Added!')
        else:
            messages.error(request, 'Error adding allocation!')
        return redirect('room_allocations')
    return render(request, 'add_room_allocation.html', {'section': 'allocations'})

def edit_room_allocation(request, id):
    if request.method == 'POST':
        payload = {
            'hostel': request.POST['hostel'],
            'floor': request.POST['floor'],
            'room_number': request.POST['room_number'],
            'room_type': request.POST['room_type'],
            'beds_left': request.POST.get('beds_left', 4),
            'user_id': request.POST['user_id'],
            'student_name': request.POST['student_name'],
            'student_roll_no': request.POST['student_roll_no'],
        }
        resp = requests.put(f'{FLASK_API}/room_allocations/{id}', json=payload)
        if resp.status_code == 200:
            messages.success(request, 'Room Allocation Updated!')
        else:
            messages.error(request, 'Error updating allocation!')
        return redirect('room_allocations')
    resp = requests.get(f'{FLASK_API}/room_allocations/{id}')
    data = resp.json() if resp.status_code == 200 else {}
    return render(request, 'edit_room_allocation.html', {'allocation': data, 'section': 'allocations'})

def delete_room_allocation(request, id):
    resp = requests.delete(f'{FLASK_API}/room_allocations/{id}')
    if resp.status_code == 200:
        messages.success(request, 'Room Allocation Deleted!')
    else:
        messages.error(request, 'Error deleting allocation!')
    return redirect('room_allocations')

# ------------------ USERS ------------------
def users(request):
    data = requests.get(f'{FLASK_API}/users').json()
    return render(request, 'users.html', {'users': data, 'section': 'users'})

def add_user(request):
    if request.method == 'POST':
        payload = {
            'name': request.POST['name'],
            'email': request.POST['email'],
            'username': request.POST['username'],
            'role': request.POST['role'],
            'password': request.POST['password'],
        }
        resp = requests.post(f'{FLASK_API}/users', json=payload)
        if resp.status_code == 201:
            messages.success(request, 'User Added!')
        else:
            messages.error(request, 'Error adding user!')
        return redirect('users')
    return render(request, 'add_user.html', {'section': 'users'})

def edit_user(request, id):
    try:
        if request.method == 'POST':
            print(f"POST data: {request.POST}")
            payload = {
                'name': request.POST.get('name', ''),
                'email': request.POST.get('email', ''),
                'username': request.POST.get('username', ''),
                'role': request.POST.get('role', ''),
            }
            print(f"Updating user {id} with payload: {payload}")
            
            # First check if user exists
            check_resp = requests.get(f'{FLASK_API}/users/{id}')
            if check_resp.status_code != 200:
                messages.error(request, 'User not found!')
                return redirect('users')
            
            # Update user
            resp = requests.put(f'{FLASK_API}/users/{id}', json=payload)
            if resp.status_code == 200:
                messages.success(request, 'User Updated Successfully!')
            else:
                error_msg = resp.json().get('message', 'Error updating user!')
                messages.error(request, f'Error: {error_msg}')
                print(f"Error updating user {id}: Status {resp.status_code}")
                print(f"Response: {resp.text}")
            return redirect('users')
        
        print(f"Fetching user {id} details")
        resp = requests.get(f'{FLASK_API}/users/{id}')
        if resp.status_code == 200:
            data = resp.json()
            print(f"User data fetched: {data}")
            return render(request, 'edit_user.html', {'user': data, 'section': 'users'})
        else:
            messages.error(request, 'User not found!')
            return redirect('users')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        print(f"Request error editing user {id}: {str(e)}")
        return redirect('users')
    except Exception as e:
        messages.error(request, f'Unexpected error: {str(e)}')
        print(f"Unexpected error editing user {id}: {str(e)}")
        return redirect('users')

def delete_user(request, id):
    try:
        resp = requests.delete(f'{FLASK_API}/users/{id}')
        if resp.status_code == 200:
            messages.success(request, 'User Deleted!')
        else:
            error_msg = resp.json().get('message', 'Error deleting user!')
            messages.error(request, f'Error: {error_msg}')
            print(f"Error deleting user {id}: Status {resp.status_code}")
            print(f"Response: {resp.text}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        print(f"Request error deleting user {id}: {str(e)}")
    except Exception as e:
        messages.error(request, f'Unexpected error: {str(e)}')
        print(f"Unexpected error deleting user {id}: {str(e)}")
    return redirect('users')

# ------------------ FEEDBACKS ------------------
def feedbacks(request):
    data = requests.get(f'{FLASK_API}/feedbacks').json()
    return render(request, 'feedbacks.html', {'feedbacks': data, 'section': 'feedbacks'})

def add_feedback(request):
    if request.method == 'POST':
        payload = {
            'first_name': request.POST['first_name'],
            'last_name': request.POST['last_name'],
            'email': request.POST['email'],
            'environment': request.POST['environment'],
            'service_rating': request.POST['service_rating'],
            'description': request.POST['description'],
            'hostel': request.POST['hostel'],
        }
        resp = requests.post(f'{FLASK_API}/feedbacks', json=payload)
        if resp.status_code == 201:
            messages.success(request, 'Feedback Added!')
        else:
            messages.error(request, 'Error adding feedback!')
        return redirect('feedbacks')
    return render(request, 'add_feedback.html', {'section': 'feedbacks'})

def edit_feedback(request, id):
    if request.method == 'POST':
        payload = {
            'first_name': request.POST['first_name'],
            'last_name': request.POST['last_name'],
            'email': request.POST['email'],
            'environment': request.POST['environment'],
            'service_rating': request.POST['service_rating'],
            'description': request.POST['description'],
            'hostel': request.POST['hostel'],
        }
        resp = requests.put(f'{FLASK_API}/feedbacks/{id}', json=payload)
        if resp.status_code == 200:
            messages.success(request, 'Feedback Updated!')
        else:
            messages.error(request, 'Error updating feedback!')
        return redirect('feedbacks')
    resp = requests.get(f'{FLASK_API}/feedbacks/{id}')
    data = resp.json() if resp.status_code == 200 else {}
    return render(request, 'edit_feedback.html', {'feedback': data, 'section': 'feedbacks'})

def delete_feedback(request, id):
    try:
        resp = requests.delete(f'{FLASK_API}/feedbacks/{id}')
        if resp.status_code == 200:
            messages.success(request, 'Feedback Deleted!')
        else:
            error_msg = resp.json().get('message', 'Error deleting feedback!')
            messages.error(request, f'Error: {error_msg}')
            print(f"Error deleting feedback {id}: Status {resp.status_code}")
            print(f"Response: {resp.text}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        print(f"Request error deleting feedback {id}: {str(e)}")
    except Exception as e:
        messages.error(request, f'Unexpected error: {str(e)}')
        print(f"Unexpected error deleting feedback {id}: {str(e)}")
    return redirect('feedbacks')

# ------------------ REQUESTS ------------------
def requests_list(request):
    data = requests.get(f'{FLASK_API}/requests').json()
    return render(request, 'requests.html', {'requests': data, 'section': 'requests'})

def add_request(request):
    if request.method == 'POST':
        payload = {
            'type': request.POST['type'],
            'maintenance_type': request.POST.get('maintenance_type', ''),
            'complaint_type': request.POST.get('complaint_type', ''),
            'user_id': request.POST['user_id'],
            'room_number': request.POST['room_number'],
            'details': request.POST['details'],
            'status': request.POST.get('status', 'pending'),
        }
        resp = requests.post(f'{FLASK_API}/requests', json=payload)
        if resp.status_code == 201:
            messages.success(request, 'Request Added!')
        else:
            messages.error(request, 'Error adding request!')
        return redirect('requests_list')
    return render(request, 'add_request.html', {'section': 'requests'})

def edit_request(request, id):
    if request.method == 'POST':
        payload = {
            'type': request.POST['type'],
            'maintenance_type': request.POST.get('maintenance_type', ''),
            'complaint_type': request.POST.get('complaint_type', ''),
            'user_id': request.POST['user_id'],
            'room_number': request.POST['room_number'],
            'details': request.POST['details'],
            'status': request.POST.get('status', 'pending'),
        }
        resp = requests.put(f'{FLASK_API}/requests/{id}', json=payload)
        if resp.status_code == 200:
            messages.success(request, 'Request Updated!')
        else:
            messages.error(request, 'Error updating request!')
        return redirect('requests_list')
    resp = requests.get(f'{FLASK_API}/requests/{id}')
    data = resp.json() if resp.status_code == 200 else {}
    return render(request, 'edit_request.html', {'request_obj': data, 'section': 'requests'})

def delete_request(request, id):
    resp = requests.delete(f'{FLASK_API}/requests/{id}')
    if resp.status_code == 200:
        messages.success(request, 'Request Deleted!')
    else:
        messages.error(request, 'Error deleting request!')
    return redirect('requests_list')

def room_allocation_page(request):
    try:
        # Get room allocations from Flask API
        room_allocations = safe_json(f'{FLASK_API}/room_allocations')
        print(f"Fetched {len(room_allocations)} room allocations from Flask API")
        
        # Get available rooms from Flask API
        available_rooms = safe_json(f'{FLASK_API}/get_available_rooms')
        print(f"Fetched available rooms data from Flask API")
        
        return render(request, 'room_allocation.html', {
            'room_allocations': room_allocations,
            'available_rooms': available_rooms,
            'section': 'room_allocation',
            'user': request.user
        })
    except Exception as e:
        print(f"Error in room_allocation_page: {str(e)}")
        messages.error(request, f'Error loading available rooms: {str(e)}')
        return render(request, 'room_allocation.html', {
            'room_allocations': [],
            'available_rooms': [],
            'section': 'room_allocation',
            'user': request.user
        })

def submit_feedback_page(request):
    return render(request, 'submit_feedback.html', {'section': 'feedback'})

def get_user(request, id):
    try:
        resp = requests.get(f'{FLASK_API}/users/{id}')
        if resp.status_code == 200:
            return JsonResponse(resp.json())
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


