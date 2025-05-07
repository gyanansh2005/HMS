from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from django.contrib import messages
from django.contrib.auth import get_user_model
from .api_utils import api_get, api_post, api_put, api_delete
from .serializers import (
    UserSerializer, StudentProfileSerializer, ComplaintSerializer,
    FeedbackSerializer, HostelSerializer, RoomAllocationSerializer
)
import logging

# Configure logging
logger = logging.getLogger(__name__)
CustomUser = get_user_model()

@login_required
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def dashboard(request):
    if request.method == 'POST':
        # Handle Create or Update based on resource
        resource = request.POST.get('resource')
        serializer = None
        data = request.POST.dict()
        
        if resource == 'user':
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                try:
                    if 'id' in data:
                        # Update existing user
                        user = CustomUser.objects.get(id=data['id'])
                        user.first_name = validated_data.get('first_name', user.first_name)
                        user.last_name = validated_data.get('last_name', user.last_name)
                        user.email = validated_data.get('email', user.email)
                        user.roll_number = validated_data.get('roll_number', user.roll_number)
                        user.is_staff = validated_data.get('is_staff', user.is_staff)
                        user.is_superuser = validated_data.get('is_superuser', user.is_superuser)
                        password = validated_data.get('password')
                        if password:
                            user.set_password(password)
                        user.save()
                        logger.info(f"Updated user {user.email} with ID {user.id}")
                        messages.success(request, 'User updated successfully!')
                    else:
                        # Create new user
                        user = CustomUser(
                            first_name=validated_data['first_name'],
                            last_name=validated_data['last_name'],
                            email=validated_data['email'],
                            roll_number=validated_data.get('roll_number', ''),
                            is_staff=validated_data.get('is_staff', False),
                            is_superuser=validated_data.get('is_superuser', False)
                        )
                        password = validated_data.get('password')
                        if password:
                            user.set_password(password)
                        else:
                            logger.error("Password required for new user")
                            messages.error(request, 'Password is required for new users')
                            return redirect('dashboard')
                        user.save()
                        logger.info(f"Created user {user.email} with ID {user.id}")
                        messages.success(request, 'User created successfully!')
                    return redirect('dashboard')
                except CustomUser.DoesNotExist:
                    logger.error(f"User ID {data.get('id')} not found")
                    messages.error(request, 'User not found')
                    return redirect('dashboard')
                except Exception as e:
                    logger.error(f"Error saving user: {str(e)}")
                    messages.error(request, f'Failed to save user: {str(e)}')
                    return redirect('dashboard')
            logger.error(f"Serializer errors for user: {serializer.errors}")
            messages.error(request, serializer.errors)
            return redirect('dashboard')
        
        elif resource == 'complaint':
            serializer = ComplaintSerializer(data=data)
            data['user_id'] = request.user.id
            endpoint = f"/api/v1/complaints/{data.get('id')}" if 'id' in data else '/api/v1/complaints'
        elif resource == 'feedback':
            serializer = FeedbackSerializer(data=data)
            data['user_id'] = request.user.id
            endpoint = f"/api/v1/feedbacks/{data.get('id')}" if 'id' in data else '/api/v1/feedbacks'
        elif resource == 'allocation':
            serializer = RoomAllocationSerializer(data=data)
            data['user_id'] = request.user.id
            endpoint = f"/api/v1/allocations/{data.get('id')}" if 'id' in data else '/api/v1/allocations'
        
        if resource != 'user' and serializer and serializer.is_valid():
            logger.debug(f"Sending data to {endpoint}: {serializer.validated_data}")
            if 'id' in data:
                response = api_put(endpoint, serializer.validated_data, request)
            else:
                response = api_post(endpoint, serializer.validated_data, request)
            if response:
                if 'error' in response:
                    logger.error(f"API error saving {resource}: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, f'{resource.capitalize()} saved successfully!')
                return redirect('dashboard')
            logger.error(f"API call to {endpoint} failed, response is None")
            messages.error(request, f'Failed to save {resource}: API call returned no response. Check server logs.')
            return redirect('dashboard')
        if resource != 'user':
            logger.error(f"Serializer errors for {resource}: {serializer.errors if serializer else 'No serializer'}")
            messages.error(request, serializer.errors if serializer else 'Invalid resource')
            return redirect('dashboard')
    
    elif request.method == 'DELETE':
        # Handle Delete
        resource = request.GET.get('resource')
        resource_id = request.GET.get('id')
        if resource == 'user' and resource_id:
            try:
                user = CustomUser.objects.get(id=resource_id)
                user.delete()
                logger.info(f"Deleted user with ID {resource_id}")
                messages.success(request, 'User deleted successfully!')
                return redirect('dashboard')
            except CustomUser.DoesNotExist:
                logger.error(f"User ID {resource_id} not found")
                messages.error(request, 'User not found')
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Error deleting user: {str(e)}")
                messages.error(request, f'Failed to delete user: {str(e)}')
                return redirect('dashboard')
        
        if resource and resource_id:
            endpoint = f"/api/v1/{resource}s/{resource_id}"
            response = api_delete(endpoint, request)
            if response:
                if 'error' in response:
                    logger.error(f"API error deleting {resource}: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, f'{resource.capitalize()} deleted successfully!')
                return redirect('dashboard')
            logger.error(f"API delete call to {endpoint} failed")
            messages.error(request, f'Failed to delete {resource}: API call returned no response')
            return redirect('dashboard')
        messages.error(request, 'Resource or ID missing')
        return redirect('dashboard')
    
    # Handle Read (GET)
    users = api_get('/api/v1/users',request)or []
    complaints = api_get('/api/v1/complaints', request) or []
    feedbacks = api_get('/api/v1/feedbacks', request) or []
    allocations = api_get('/api/v1/allocations', request) or []
    return render(request, 'dashboard.html', {
        'user_count': len(users),
        'complaint_count': len(complaints),
        'feedback_count': len(feedbacks),
        'allocation_count': len(allocations),
        'users': users,
        'complaints': complaints,
        'feedbacks': feedbacks,
        'allocations': allocations,
        'active_tab': 'dashboard'
    })

@login_required
@api_view(['GET', 'POST'])
def users(request):
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            if 'id' in data:
                # Update existing user
                response = api_put(f"/api/v1/users/{data['id']}", data, request)
            else:
                # Create new user
                response = api_post('/api/v1/users', data, request)
            
            if response:
                if 'error' in response:
                    logger.error(f"API error saving user: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, 'User saved successfully!')
                return redirect('dashboard')
            logger.error(f"API call to /api/v1/users failed, response is None")
            messages.error(request, 'Failed to save user: API call returned no response')
            return redirect('dashboard')
        except Exception as e:
            logger.error(f"Error in users view: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('dashboard')
    
    # GET request - fetch users
    users = api_get('/api/v1/users', request) or []
    return render(request, 'dashboard.html', {
        'users': users,
        'active_tab': 'users'
    })

@login_required
@api_view(['GET'])
def user_detail(request, id):
    try:
        response = api_get(f"/api/v1/users/{id}", request)
        if response:
            return Response(response)
        return Response({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching user details: {str(e)}")
        return Response({'error': str(e)}, status=500)

@login_required
@api_view(['GET', 'POST'])
def complaints(request):
    if request.method == 'POST':
        serializer = ComplaintSerializer(data=request.POST)
        if serializer.is_valid():
            data = serializer.validated_data
            data['user_id'] = request.user.id
            logger.debug(f"Sending data to /api/v1/complaints: {data}")
            if 'id' in request.POST:
                response = api_put(f"/api/v1/complaints/{request.POST['id']}", data, request)
            else:
                response = api_post('/api/v1/complaints', data, request)
            if response:
                if 'error' in response:
                    logger.error(f"API error saving complaint: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, 'Complaint saved successfully!')
                return redirect('complaints')
            logger.error(f"API call to /api/v1/complaints failed, response is None")
            messages.error(request, 'Failed to save complaint: API call returned no response. Check server logs.')
            return redirect('complaints')
        logger.error(f"Serializer errors for complaint: {serializer.errors}")
        messages.error(request, serializer.errors)
        return redirect('complaints')
    complaints = api_get('/api/v1/complaints', request) or []
    return render(request, 'complaints.html', {'complaints': complaints})

@login_required
@api_view(['GET', 'POST'])
def feedback(request):
    if request.method == 'POST':
        serializer = FeedbackSerializer(data=request.POST)
        if serializer.is_valid():
            data = serializer.validated_data
            data['user_id'] = request.user.id
            logger.debug(f"Sending data to /api/v1/feedbacks: {data}")
            if 'id' in request.POST:
                response = api_put(f"/api/v1/feedbacks/{request.POST['id']}", data, request)
            else:
                response = api_post('/api/v1/feedbacks', data, request)
            if response:
                if 'error' in response:
                    logger.error(f"API error saving feedback: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, 'Feedback saved successfully!')
                return redirect('feedback')
            logger.error(f"API call to /api/v1/feedbacks failed, response is None")
            messages.error(request, 'Failed to save feedback: API call returned no response. Check server logs.')
            return redirect('feedback')
        logger.error(f"Serializer errors for feedback: {serializer.errors}")
        messages.error(request, serializer.errors)
        return redirect('feedback')
    feedbacks = api_get('/api/v1/feedbacks', request) or []
    return render(request, 'feedback.html', {'feedbacks': feedbacks})

@login_required
@api_view(['GET', 'POST'])
def allocations(request):
    if request.method == 'POST':
        serializer = RoomAllocationSerializer(data=request.POST)
        if serializer.is_valid():
            data = serializer.validated_data
            data['user_id'] = request.user.id
            logger.debug(f"Sending data to /api/v1/allocations: {data}")
            if 'id' in request.POST:
                response = api_put(f"/api/v1/allocations/{request.POST['id']}", data, request)
            else:
                response = api_post('/api/v1/allocations', data, request)
            if response:
                if 'error' in response:
                    logger.error(f"API error saving allocation: {response['error']}")
                    messages.error(request, response['error'])
                else:
                    messages.success(request, 'Allocation saved successfully!')
                return redirect('allocations')
            logger.error(f"API call to /api/v1/allocations failed, response is None")
            messages.error(request, 'Failed to save allocation: API call returned no response. Check server logs.')
            return redirect('allocations')
        logger.error(f"Serializer errors for allocation: {serializer.errors}")
        messages.error(request, serializer.errors)
        return redirect('allocations')
    allocations = api_get('/api/v1/allocations', request) or []
    rooms = api_get('/api/v1/available_rooms?hostel_id=1&floor=0', request) or {}
    return render(request, 'allocations.html', {'allocations': allocations, 'rooms': rooms})

@login_required
@api_view(['POST'])
def delete_user(request, id):
    try:
        response = api_delete(f"/api/v1/users/{id}", request)
        if response is True:
            messages.success(request, 'User deleted successfully!')
        else:
            logger.error(f"API delete call to /api/v1/users/{id} failed")
            messages.error(request, 'Failed to delete user')
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        messages.error(request, f'Failed to delete user: {str(e)}')
    return redirect('dashboard')

@login_required
@api_view(['POST'])
def delete_complaint(request, id):
    response = api_delete(f"/api/v1/complaints/{id}", request)
    if response is True:
        messages.success(request, 'Complaint deleted successfully!')
    else:
        logger.error(f"API delete call to /api/v1/complaints/{id} failed")
        messages.error(request, 'Failed to delete complaint')
    return redirect('dashboard')

@login_required
@api_view(['POST'])
def delete_feedback(request, id):
    response = api_delete(f"/api/v1/feedbacks/{id}", request)
    if response is True:
        messages.success(request, 'Feedback deleted successfully!')
    else:
        logger.error(f"API delete call to /api/v1/feedbacks/{id} failed")
        messages.error(request, 'Failed to delete feedback')
    return redirect('dashboard')

@login_required
@api_view(['DELETE'])
def delete_allocation(request, id):
    response = api_delete(f"/api/v1/allocations/{id}", request)
    if response:
        if 'error' in response:
            logger.error(f"API error deleting allocation: {response['error']}")
            messages.error(request, response['error'])
        else:
            messages.success(request, 'Allocation deleted successfully!')
        return redirect('allocations')
    logger.error(f"API delete call to /api/v1/allocations/{id} failed")
    messages.error(request, 'Failed to delete allocation: API call returned no response')
    return redirect('allocations')