import requests
from django.conf import settings

def api_get(endpoint, request=None):
    try:
        # Change BASE_URL to API_BASE_URL
        response = requests.get(f"{settings.API_BASE_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def api_post(endpoint, data, request=None):
    try:
        # Change BASE_URL to API_BASE_URL
        response = requests.post(f"{settings.API_BASE_URL}{endpoint}", json=data)
        return response.json() if response.status_code in [200, 201] else None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def api_put(endpoint, data, request=None):
    try:
        # Change BASE_URL to API_BASE_URL
        response = requests.put(f"{settings.API_BASE_URL}{endpoint}", json=data)
        return response.json() if response.status_code in [200, 201] else None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def api_delete(endpoint, request=None):
    try:
        # Change BASE_URL to API_BASE_URL
        response = requests.delete(f"{settings.API_BASE_URL}{endpoint}")
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"API Error: {e}")
        return False