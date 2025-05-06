import os
from app import db, Hostel, Room, app

def seed_hostels():
    with app.app_context():
        # Delete existing data
        Room.query.delete()
        Hostel.query.delete()
        db.session.commit()
        print('Cleared existing hostel and room data')

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
            hostel = Hostel(
                name=hostel_data['name'],
                total_floors=hostel_data['total_floors'],
                main_image=hostel_data['main_image'],
                features=hostel_data['features']
            )
            db.session.add(hostel)
            db.session.flush()  # Get hostel.id

            # Create 10 rooms per floor (4 singles, 3 doubles, 3 four-sharings)
            for floor in range(1, hostel.total_floors + 1):
                # Single Rooms (4 instances)
                for i in range(1, 5):  # Rooms 01 to 04
                    room = Room(
                        hostel_id=hostel.id,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",
                        room_type='single',
                        ac_type='ac' if i % 2 == 0 else 'non_ac',
                        total_beds=1,
                        price=15000 if i % 2 == 0 else 12000,
                        amenities="Private Bathroom, Work Desk, WiFi, " +
                                  ("AC, Smart TV" if i % 2 == 0 else "Fan, LED Lighting")
                    )
                    db.session.add(room)

                # Double Rooms (3 instances)
                for i in range(5, 8):  # Rooms 05 to 07
                    room = Room(
                        hostel_id=hostel.id,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",
                        room_type='double',
                        ac_type='ac' if (i - 4) % 2 == 0 else 'non_ac',
                        total_beds=2,
                        price=9000 if (i - 4) % 2 == 0 else 7000,
                        amenities="Shared Desk, Wardrobe, WiFi, " +
                                  ("AC" if (i - 4) % 2 == 0 else "Fan")
                    )
                    db.session.add(room)

                # 4-Sharing Rooms (3 instances)
                for i in range(8, 11):  # Rooms 08 to 10
                    room = Room(
                        hostel_id=hostel.id,
                        floor=floor,
                        room_number=f"{floor}{i:02d}",
                        room_type='four',
                        ac_type='non_ac' if (i - 7) % 2 == 0 else 'ac',
                        total_beds=4,
                        price=5000 if (i - 7) % 2 == 0 else 6000,
                        amenities="Bunk Beds, Shared Area, WiFi, " +
                                  ("AC" if (i - 7) % 2 == 0 else "Fan")
                    )
                    db.session.add(room)

        db.session.commit()
        print('Seeded hostels and rooms successfully!')

if __name__ == "__main__":
    seed_hostels()