import requests
from django.contrib import messages

class APIClient:
    def __init__(self, base_url, request=None):
        self.base_url = base_url
        self.request = request  # For displaying messages

    def get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.request:
                messages.error(self.request, f"Error fetching data: {str(e)}")
            return None

    def post(self, endpoint, data):
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.request:
                messages.error(self.request, f"Error creating data: {str(e)}")
            return None

    def put(self, endpoint, data):
        try:
            response = requests.put(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.request:
                messages.error(self.request, f"Error updating data: {str(e)}")
            return None

    def delete(self, endpoint):
        try:
            response = requests.delete(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.request:
                messages.error(self.request, f"Error deleting data: {str(e)}")
            return None