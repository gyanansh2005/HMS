import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RoomAllocationSerializer, UserSerializer, FeedbackSerializer, RequestSerializer
)

FLASK_API = 'http://localhost:5000/api'

@api_view(['GET', 'POST'])
def room_allocation_list(request):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/room_allocations')
        data = resp.json() if resp.status_code == 200 else []
        serializer = RoomAllocationSerializer(data, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        resp = requests.post(f'{FLASK_API}/room_allocations', json=request.data)
        return Response(resp.json(), status=resp.status_code)

@api_view(['GET', 'PUT', 'DELETE'])
def room_allocation_detail(request, pk):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/room_allocations/{pk}')
        data = resp.json() if resp.status_code == 200 else {}
        serializer = RoomAllocationSerializer(data)
        return Response(serializer.data)
    elif request.method == 'PUT':
        resp = requests.put(f'{FLASK_API}/room_allocations/{pk}', json=request.data)
        return Response(resp.json(), status=resp.status_code)
    elif request.method == 'DELETE':
        resp = requests.delete(f'{FLASK_API}/room_allocations/{pk}')
        return Response({}, status=resp.status_code)

@api_view(['GET', 'POST'])
def user_list(request):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/users')
        data = resp.json() if resp.status_code == 200 else []
        serializer = UserSerializer(data, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        resp = requests.post(f'{FLASK_API}/users', json=request.data)
        return Response(resp.json(), status=resp.status_code)

@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, pk):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/users/{pk}')
        data = resp.json() if resp.status_code == 200 else {}
        serializer = UserSerializer(data)
        return Response(serializer.data)
    elif request.method == 'PUT':
        resp = requests.put(f'{FLASK_API}/users/{pk}', json=request.data)
        return Response(resp.json(), status=resp.status_code)
    elif request.method == 'DELETE':
        resp = requests.delete(f'{FLASK_API}/users/{pk}')
        return Response({}, status=resp.status_code)

@api_view(['GET', 'POST'])
def feedback_list(request):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/feedbacks')
        data = resp.json() if resp.status_code == 200 else []
        serializer = FeedbackSerializer(data, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        resp = requests.post(f'{FLASK_API}/feedbacks', json=request.data)
        return Response(resp.json(), status=resp.status_code)

@api_view(['GET', 'PUT', 'DELETE'])
def feedback_detail(request, pk):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/feedbacks/{pk}')
        data = resp.json() if resp.status_code == 200 else {}
        serializer = FeedbackSerializer(data)
        return Response(serializer.data)
    elif request.method == 'PUT':
        resp = requests.put(f'{FLASK_API}/feedbacks/{pk}', json=request.data)
        return Response(resp.json(), status=resp.status_code)
    elif request.method == 'DELETE':
        resp = requests.delete(f'{FLASK_API}/feedbacks/{pk}')
        return Response({}, status=resp.status_code)

@api_view(['GET', 'POST'])
def request_list(request):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/requests')
        data = resp.json() if resp.status_code == 200 else []
        serializer = RequestSerializer(data, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        resp = requests.post(f'{FLASK_API}/requests', json=request.data)
        return Response(resp.json(), status=resp.status_code)

@api_view(['GET', 'PUT', 'DELETE'])
def request_detail(request, pk):
    if request.method == 'GET':
        resp = requests.get(f'{FLASK_API}/requests/{pk}')
        data = resp.json() if resp.status_code == 200 else {}
        serializer = RequestSerializer(data)
        return Response(serializer.data)
    elif request.method == 'PUT':
        resp = requests.put(f'{FLASK_API}/requests/{pk}', json=request.data)
        return Response(resp.json(), status=resp.status_code)
    elif request.method == 'DELETE':
        resp = requests.delete(f'{FLASK_API}/requests/{pk}')
        return Response({}, status=resp.status_code)