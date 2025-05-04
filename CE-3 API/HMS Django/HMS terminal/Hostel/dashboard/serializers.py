from rest_framework import serializers

class RoomAllocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    hostel = serializers.CharField()
    floor = serializers.IntegerField()
    room_number = serializers.IntegerField()
    room_type = serializers.CharField()
    beds_left = serializers.IntegerField()
    user_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_roll_no = serializers.CharField()

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    role = serializers.CharField()
    username = serializers.CharField()

class FeedbackSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    environment = serializers.CharField()
    service_rating = serializers.IntegerField()
    description = serializers.CharField()
    hostel = serializers.CharField()
    created_at = serializers.CharField()

class RequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    maintenance_type = serializers.CharField(allow_null=True, required=False)
    complaint_type = serializers.CharField(allow_null=True, required=False)
    user_id = serializers.IntegerField()
    room_number = serializers.CharField()
    details = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.CharField()
