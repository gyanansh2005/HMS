from django.db import migrations

def create_initial_data(apps, schema_editor):
    Hostel = apps.get_model('Rooms', 'Hostel')
    Room = apps.get_model('Rooms', 'Room')
    
    # Clear any existing data first
    Room.objects.all().delete()
    Hostel.objects.all().delete()
    
    # Create 4 hostels
    campuses = ['Campus 1', 'Campus 2', 'Campus 3', 'Campus 4']
    for i, campus in enumerate(campuses, start=1):
        Hostel.objects.create(
            name=f'Hostel {chr(64+i)}',  # A, B, C, D
            campus=campus
        )
    
    # Create rooms for each hostel
    for hostel in Hostel.objects.all():
        for floor in range(1, 4):  # 3 floors
            # 5 single rooms (101-105)
            for i in range(1, 6):
                Room.objects.create(
                    hostel=hostel,
                    floor=floor,
                    room_number=f"{floor}0{i}",
                    room_type="single",
                    capacity=1
                )
            
            # 5 double rooms (106-110)
            for i in range(6, 11):
                Room.objects.create(
                    hostel=hostel,
                    floor=floor,
                    room_number=f"{floor}{i}",
                    room_type="double",
                    capacity=2
                )
            
            # 5 four-sharing rooms (111-115)
            for i in range(11, 16):
                Room.objects.create(
                    hostel=hostel,
                    floor=floor,
                    room_number=f"{floor}{i}",
                    room_type="four",
                    capacity=4
                )

def reverse_data(apps, schema_editor):
    Hostel = apps.get_model('Rooms', 'Hostel')
    Hostel.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('Rooms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_data),
    ]