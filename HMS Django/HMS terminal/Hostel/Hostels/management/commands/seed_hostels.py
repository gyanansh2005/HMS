from django.core.management.base import BaseCommand
from Hostels.models import Hostel, Room

class Command(BaseCommand):
    help = 'Creates premium hostel data with enhanced features'

    def handle(self, *args, **kwargs):
        hostels_data = [
            {
                'name': "CampusNest Elite",
                'floors': 8,
                'features': "Infinity Rooftop Lounge, Olympic-size Pool, Robotics Housekeeping",
                'image': 'premium-hostel-1.jpg',
                'tagline': "Luxury Redefined"
            },
            {
                'name': "Scholar's Horizon",
                'floors': 6,
                'features': "AI Study Assistant, Virtual Reality Lounge, Organic Cafe",
                'image': 'premium-hostel-2.jpg',
                'tagline': "Smart Living"
            },
            {
                'name': "Green Valley Eco",
                'floors': 5,
                'features': "Solar Powered, Vertical Gardens, Electric Shuttle Service",
                'image': 'eco-hostel.jpg',
                'tagline': "Sustainable Living"
            },
            {
                'name': "TechHub Residences",
                'floors': 7,
                'features': "Gaming Arena, 3D Printing Lab, Coding Pods",
                'image': 'tech-hostel.jpg',
                'tagline': "Innovators' Paradise"
            }
        ]

        room_types = [
            {'code': 'suite', 'name': 'Executive Suite', 'beds': 1},
            {'code': 'deluxe', 'name': 'Deluxe Double', 'beds': 2},
            {'code': 'smart', 'name': 'Smart Quad', 'beds': 4}
        ]

        for hostel_data in hostels_data:
            hostel = Hostel.objects.create(
                name=hostel_data['name'],
                total_floors=hostel_data['floors'],
                features=hostel_data['features']
            )

            # Create unique rooms for each floor
            for floor in range(1, hostel_data['floors'] + 1):
                for idx, room_type in enumerate(room_types):
                    for ac_type in ['ac', 'non_ac']:
                        room_number = f"{floor}{room_type['code'][0].upper()}{idx + 1}"
                        Room.objects.create(
                            hostel=hostel,
                            floor=floor,
                            room_number=room_number,
                            room_type=room_type['code'],
                            ac_type=ac_type,
                            total_beds=room_type['beds'],
                            price=self.calculate_price(room_type['code'], ac_type, hostel_data['name']),
                            amenities=self.get_amenities(room_type['code'], ac_type),
                            occupied_beds=0
                        )

            self.stdout.write(self.style.SUCCESS(f'Created premium hostel: {hostel_data["name"]}'))

    def calculate_price(self, room_type, ac_type, hostel_name):
        base_prices = {
            'suite': 15000,
            'deluxe': 9000,
            'smart': 6000
        }
        ac_surcharge = 2000 if ac_type == 'ac' else 0
        premium_bonus = 3000 if 'Elite' in hostel_name else 1500 if 'TechHub' in hostel_name else 0
        return base_prices[room_type] + ac_surcharge + premium_bonus

    def get_amenities(self, room_type, ac_type):
        amenities = {
            'suite': ["King-size bed", "Mini-bar", "Smart TV", "Jacuzzi"],
            'deluxe': ["Queen beds", "Study desk", "Mini-fridge"],
            'smart': ["Loft beds", "Charging stations", "Smart locks"]
        }
        base = amenities[room_type]
        base.append("AC" if ac_type == 'ac' else "Premium Ventilation")
        return ", ".join(base)