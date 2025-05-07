from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    roll_number = serializers.CharField(max_length=20, allow_blank=True, required=False)
    password = serializers.CharField(max_length=128, write_only=True, required=False)
    is_staff = serializers.BooleanField(default=False)
    is_superuser = serializers.BooleanField(default=False)

    def validate_email(self, value):
        if '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value

class StudentProfileSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    contact_number = serializers.CharField(max_length=15, allow_blank=True, required=False)
    profile_picture = serializers.URLField(allow_blank=True, required=False)
    bio = serializers.CharField(allow_blank=True, required=False)

    def validate_user_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("User ID must be positive")
        return value

class ComplaintSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    request_type = serializers.ChoiceField(choices=['complaint', 'maintenance'])
    room_number = serializers.CharField(max_length=10)
    category = serializers.CharField(max_length=50)
    details = serializers.CharField()
    status = serializers.ChoiceField(choices=['pending', 'resolved'], default='pending')

    def validate_room_number(self, value):
        if not value:
            raise serializers.ValidationError("Room number is required")
        return value

class FeedbackSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True, required=False)
    environment_rating = serializers.CharField(max_length=20)
    service_rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField()
    hostel = serializers.CharField(max_length=50)

    def validate_service_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Service rating must be between 1 and 5")
        return value

class HostelSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    total_floors = serializers.IntegerField(min_value=1)
    main_image = serializers.URLField(allow_blank=True, required=False)
    features = serializers.CharField(allow_blank=True, required=False)

    def validate_total_floors(self, value):
        if value < 1:
            raise serializers.ValidationError("Total floors must be at least 1")
        return value

class RoomAllocationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    room_id = serializers.IntegerField()
    room_number = serializers.CharField(max_length=10)
    room_type = serializers.CharField(max_length=50)
    hostel_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['pending', 'confirmed', 'cancelled'], default='pending')

    def validate_room_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("Room ID must be positive")
        return value

    def validate_hostel_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("Hostel ID must be positive")
        return value