from django.core.management.base import BaseCommand
from Hostels.models import Hostel, Room

class Command(BaseCommand):
    help = 'Creates hostel data with single, double, and 4-sharing rooms, 10 rooms per floor'

    def handle(self, *args, **kwargs):
        # Delete existing data
        Hostel.objects.all().delete()
        Room.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing hostel and room data'))

        hostels_data = [
            {
                'name': "CampusNest Elite",
                'total_floors': 10,
                'features': "Luxury Amenities, Rooftop Terrace, 24/7 Gym, Smart Lock Systems, High-Speed WiFi, Study Lounges",
                'main_image': 'hostels/campusnest_elite.jpg'
            },
            {
                'name': "Scholar's Horizon",
                'total_floors': 8,
                'features': "Quiet Study Areas, 24/7 Library Access, Coffee Bar, Career Counseling, Outdoor Seating, Seminar Rooms",
                'main_image': 'hostels/scholars_horizon.jpg'
            },
            {
                'name': "Green Valley Eco",
                'total_floors': 7,
                'features': "Solar Power, Organic Garden, Rainwater Harvesting, Eco-Friendly Materials, Yoga Deck, Recycling Stations",
                'main_image': 'hostels/green_valley.jpg'
            },
            {
                'name': "TechHub Residences",
                'total_floors': 9,
                'features': "Gaming Arena, Coding Labs, VR Zone, High-Speed Internet, Tech Workshops, 3D Printing",
                'main_image': 'hostels/techhub.jpg'
            },
            {
                'name': "Urban Retreat",
                'total_floors': 8,
                'features': "City Views, Fitness Center, Movie Theater, BBQ Area, Bike Storage, Co-Working Space",
                'main_image': 'hostels/urban_retreat.jpg'
            },
            {
                'name': "Academic Haven",
                'total_floors': 7,
                'features': "Silent Study Zones, Tutoring Center, Book Exchange, Outdoor Terrace, Meditation Garden",
                'main_image': 'hostels/academic_haven.jpg'
            },
            {
                'name': "City Pulse Residences",
                'total_floors': 9,
                'features': "Panoramic Views, Social Lounge, Art Studio, Shuttle Service, Music Room, Outdoor Cinema",
                'main_image': 'hostels/city_pulse.jpg'
            }
        ]

        for hostel_data in hostels_data:
            hostel = Hostel.objects.create(
                name=hostel_data['name'],
                total_floors=hostel_data['total_floors'],
                main_image=hostel_data['main_image'],
                features=hostel_data['features']
            )

            # Create 10 rooms per floor (4 singles, 3 doubles, 3 four-sharings)
            for floor in range(1, hostel.total_floors + 1):
                # Single Rooms (4 instances)
                for i in range(1, 5):  # Rooms 01 to 04
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 701, 702, 703, 704
                        room_type='single',
                        ac_type='ac' if i % 2 == 0 else 'non_ac',  # Alternate AC and non-AC
                        total_beds=1,
                        price=15000 if i % 2 == 0 else 12000,  # Higher for AC
                        amenities="Private Bathroom, Work Desk, WiFi, " +
                                  ("AC, Smart TV" if i % 2 == 0 else "Fan, LED Lighting")
                    )
                
                # Double Rooms (3 instances)
                for i in range(5, 8):  # Rooms 05 to 07
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 705, 706, 707
                        room_type='double',
                        ac_type='ac' if (i - 4) % 2 == 0 else 'non_ac',  # Alternate AC and non-AC
                        total_beds=2,
                        price=9000 if (i - 4) % 2 == 0 else 7000,  # Higher for AC
                        amenities="Shared Desk, Wardrobe, WiFi, " +
                                  ("AC" if (i - 4) % 2 == 0 else "Fan")
                    )
                
                # 4-Sharing Rooms (3 instances)
                for i in range(8, 11):  # Rooms 08 to 10
                    Room.objects.create(
                        hostel=hostel,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",  # e.g., 708, 709, 710
                        room_type='four',
                        ac_type='non_ac' if (i - 7) % 2 == 0 else 'ac',  # Alternate AC and non-AC
                        total_beds=4,
                        price=5000 if (i - 7) % 2 == 0 else 6000,  # Higher for AC
                        amenities="Bunk Beds, Shared Area, WiFi, " +
                                  ("AC" if (i - 7) % 2 == 0 else "Fan")
                    )

            self.stdout.write(self.style.SUCCESS(f'Created {hostel.name} with 10 rooms per floor across {hostel.total_floors} floors'))
