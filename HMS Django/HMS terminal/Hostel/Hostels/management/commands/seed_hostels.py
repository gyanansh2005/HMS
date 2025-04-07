# app1/management/commands/seed_hostels.py
from django.core.management.base import BaseCommand
from Hostels.models import Hostel, Room
import random

class Command(BaseCommand):
    help = 'Creates initial hostel data with rooms'

    def handle(self, *args, **kwargs):
        hostel_names = [
            "Golden Oak Hostel", "Sapphire Heights", "Emerald Valley Residences",
            "Royal Crest Hostel", "Silver Pine Lodgings", "Marigold Student House",
            "Horizon View Hostel", "Tranquil Woods Residences", "Summit Peak Hostel",
            "Ivory Tower Lodgings", "Crimson Maple House", "Azure Sky Hostel",
            "Prestige Student Living", "Harmony Hall Residences", "Liberty Square Hostel",
            "The Scholar's Den", "Green Valley Hostel", "Stellar Student Homes",
            "Heritage Hall Residences", "Olympia Student Hostel", "Pine Crest Lodgings",
            "The Learning Tree Hostel", "Sunrise Student Residences", "Cosmos House",
            "Victoria Court Hostel", "Golden Gates Residences", "Athena Student House",
            "North Star Hostel", "Elysium Student Living", "Zenith Heights Hostel"
        ]

        room_types = ['four', 'double', 'single']
        ac_types = ['ac', 'non_ac']
        amenities = {
            'ac': ["AC", "WiFi", "Study Desk", "Attached Bathroom", "Bed Linens"],
            'non_ac': ["Fan", "WiFi", "Study Desk", "Common Bathroom", "Bed Linens"]
        }

        for name in hostel_names:
            hostel = Hostel.objects.create(
                name=name,
                total_floors=10
            )

            for floor in range(1, 11):
                # Create 5 rooms of each type per AC category
                for room_type in room_types:
                    for ac_type in ac_types:
                        for room_num in range(1, 6):
                            room = Room(
                                hostel=hostel,
                                floor=floor,
                                room_number=f"{floor}{room_type[:1]}{room_num}",
                                room_type=room_type,
                                ac_type=ac_type,
                                total_beds=4 if room_type == 'four' else 2 if room_type == 'double' else 1,
                                occupied_beds=0,
                                price=self.get_price(room_type, ac_type),
                                amenities=", ".join(amenities[ac_type])
                            )
                            room.save()

            self.stdout.write(self.style.SUCCESS(f'Created hostel: {name}'))

    def get_price(self, room_type, ac_type):
        base_prices = {
            'four': 4000,
            'double': 6000,
            'single': 10000
        }
        ac_surcharge = 1500 if ac_type == 'ac' else 0
        return base_prices[room_type] + ac_surcharge