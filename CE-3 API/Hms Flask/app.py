from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_restful import Api, Resource
from flask_cors import CORS
from werkzeug.exceptions import InternalServerError
import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config['SECRET_KEY'] = 'my_secret_key'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
api = Api(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --- Validation Functions ---
def validate_user_data(data, is_update=False, instance_id=None):
    errors = {}
    if not is_update or 'email' in data:
        if not data.get('email'):
            errors['email'] = 'Email is required'
        elif not isinstance(data['email'], str) or len(data['email']) > 100:
            errors['email'] = 'Invalid email'
        elif db.session.query(User).filter_by(email=data['email']).filter(User.id != instance_id if instance_id else True).first():
            errors['email'] = 'Email already exists'
    
    if not is_update or 'first_name' in data:
        if not data.get('first_name'):
            errors['first_name'] = 'First name is required'
        elif not isinstance(data['first_name'], str) or len(data['first_name']) > 100:
            errors['first_name'] = 'Invalid first name'
    
    if not is_update or 'last_name' in data:
        if not data.get('last_name'):
            errors['last_name'] = 'Last name is required'
        elif not isinstance(data['last_name'], str) or len(data['last_name']) > 100:
            errors['last_name'] = 'Invalid last name'
    
    if not is_update or 'password' in data:
        if not is_update and not data.get('password'):
            errors['password'] = 'Password is required'
        elif data.get('password') and (not isinstance(data['password'], str) or len(data['password']) < 6):
            errors['password'] = 'Password must be at least 6 characters'
    
    if 'roll_number' in data and data['roll_number']:
        if not isinstance(data['roll_number'], str) or len(data['roll_number']) > 20:
            errors['roll_number'] = 'Invalid roll number'
        elif db.session.query(User).filter_by(roll_number=data['roll_number']).filter(User.id != instance_id if instance_id else True).first():
            errors['roll_number'] = 'Roll number already exists'
    
    return errors

def validate_student_profile_data(data):
    errors = {}
    if not data.get('user_id'):
        errors['user_id'] = 'User ID is required'
    elif not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if 'contact_number' in data and data['contact_number'] and (not isinstance(data['contact_number'], str) or len(data['contact_number']) > 15):
        errors['contact_number'] = 'Invalid contact number'
    
    if 'profile_picture' in data and data['profile_picture'] and (not isinstance(data['profile_picture'], str) or len(data['profile_picture']) > 255):
        errors['profile_picture'] = 'Invalid profile picture URL'
    
    return errors

def validate_hostel_data(data):
    errors = {}
    if not data.get('name'):
        errors['name'] = 'Name is required'
    elif not isinstance(data['name'], str) or len(data['name']) > 100:
        errors['name'] = 'Invalid name'
    
    if not data.get('total_floors'):
        errors['total_floors'] = 'Total floors is required'
    elif not isinstance(data['total_floors'], int) or data['total_floors'] < 1:
        errors['total_floors'] = 'Total floors must be a positive integer'
    
    if 'main_image' in data and data['main_image'] and (not isinstance(data['main_image'], str) or len(data['main_image']) > 255):
        errors['main_image'] = 'Invalid main image URL'
    
    return errors

def validate_room_data(data):
    errors = {}
    if not data.get('hostel_id'):
        errors['hostel_id'] = 'Hostel ID is required'
    elif not db.session.query(Hostel).get(data['hostel_id']):
        errors['hostel_id'] = 'Hostel not found'
    
    if not data.get('floor') and data['floor'] != 0:
        errors['floor'] = 'Floor is required'
    elif not isinstance(data['floor'], int) or data['floor'] < 0:
        errors['floor'] = 'Floor must be a non-negative integer'
    
    if not data.get('room_number'):
        errors['room_number'] = 'Room number is required'
    elif not isinstance(data['room_number'], str) or len(data['room_number']) > 10:
        errors['room_number'] = 'Invalid room number'
    
    if not data.get('room_type'):
        errors['room_type'] = 'Room type is required'
    elif data['room_type'] not in ['four', 'double', 'single']:
        errors['room_type'] = 'Room type must be four, double, or single'
    
    if not data.get('ac_type'):
        errors['ac_type'] = 'AC type is required'
    elif data['ac_type'] not in ['ac', 'non_ac']:
        errors['ac_type'] = 'AC type must be ac or non_ac'
    
    if not data.get('total_beds'):
        errors['total_beds'] = 'Total beds is required'
    elif not isinstance(data['total_beds'], int) or data['total_beds'] < 1:
        errors['total_beds'] = 'Total beds must be a positive integer'
    
    if 'occupied_beds' in data and (not isinstance(data['occupied_beds'], int) or data['occupied_beds'] < 0):
        errors['occupied_beds'] = 'Occupied beds must be a non-negative integer'
    
    if not data.get('price'):
        errors['price'] = 'Price is required'
    elif not isinstance(data['price'], (int, float)) or data['price'] < 0:
        errors['price'] = 'Price must be a non-negative number'
    
    return errors

def validate_allocation_data(data):
    errors = {}
    if not data.get('user_id'):
        errors['user_id'] = 'User ID is required'
    elif not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if not data.get('room_id'):
        errors['room_id'] = 'Room ID is required'
    elif not db.session.query(Room).get(data['room_id']):
        errors['room_id'] = 'Room not found'
    
    if 'status' in data and data['status'] not in ['pending', 'allocated']:
        errors['status'] = 'Status must be pending or allocated'
    
    return errors

def validate_room_allocation_data(data):
    errors = {}
    if not data.get('hostel_id'):
        errors['hostel_id'] = 'Hostel ID is required'
    elif not db.session.query(Hostel).get(data['hostel_id']):
        errors['hostel_id'] = 'Hostel not found'
    
    if not data.get('floor') and data['floor'] != 0:
        errors['floor'] = 'Floor is required'
    elif not isinstance(data['floor'], int) or data['floor'] < 0:
        errors['floor'] = 'Floor must be a non-negative integer'
    
    if not data.get('room_number'):
        errors['room_number'] = 'Room number is required'
    elif not isinstance(data['room_number'], str) or len(data['room_number']) > 10:
        errors['room_number'] = 'Invalid room number'
    
    if not data.get('room_type'):
        errors['room_type'] = 'Room type is required'
    elif data['room_type'] not in ['four', 'double', 'single']:
        errors['room_type'] = 'Room type must be four, double, or single'
    
    return errors

def validate_room_change_request_data(data):
    errors = {}
    if not data.get('user_id'):
        errors['user_id'] = 'User ID is required'
    elif not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if not data.get('current_allocation_id'):
        errors['current_allocation_id'] = 'Current allocation ID is required'
    elif not db.session.query(Allocation).get(data['current_allocation_id']):
        errors['current_allocation_id'] = 'Allocation not found'
    
    if not data.get('requested_room_id'):
        errors['requested_room_id'] = 'Requested room ID is required'
    elif not db.session.query(Room).get(data['requested_room_id']):
        errors['requested_room_id'] = 'Room not found'
    
    if not data.get('reason'):
        errors['reason'] = 'Reason is required'
    
    if 'status' in data and data['status'] not in ['pending', 'approved', 'rejected']:
        errors['status'] = 'Status must be pending, approved, or rejected'
    
    return errors

def validate_fee_payment_data(data):
    errors = {}
    if not data.get('user_id'):
        errors['user_id'] = 'User ID is required'
    elif not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if not data.get('allocation_id'):
        errors['allocation_id'] = 'Allocation ID is required'
    elif not db.session.query(Allocation).get(data['allocation_id']):
        errors['allocation_id'] = 'Allocation not found'
    
    if not data.get('amount'):
        errors['amount'] = 'Amount is required'
    elif not isinstance(data['amount'], (int, float)) or data['amount'] < 0:
        errors['amount'] = 'Amount must be a non-negative number'
    
    if not data.get('transaction_id'):
        errors['transaction_id'] = 'Transaction ID is required'
    elif not isinstance(data['transaction_id'], str) or len(data['transaction_id']) > 100:
        errors['transaction_id'] = 'Invalid transaction ID'
    elif db.session.query(FeePayment).filter_by(transaction_id=data['transaction_id']).first():
        errors['transaction_id'] = 'Transaction ID already exists'
    
    if 'status' in data and data['status'] not in ['pending', 'completed', 'failed']:
        errors['status'] = 'Status must be pending, completed, or failed'
    
    return errors

def validate_complaint_maintenance_data(data):
    errors = {}
    if not data.get('user_id'):
        errors['user_id'] = 'User ID is required'
    elif not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if not data.get('request_type'):
        errors['request_type'] = 'Request type is required'
    elif data['request_type'] not in ['complaint', 'maintenance']:
        errors['request_type'] = 'Request type must be complaint or maintenance'
    
    if not data.get('room_number'):
        errors['room_number'] = 'Room number is required'
    elif not isinstance(data['room_number'], str) or len(data['room_number']) > 10:
        errors['room_number'] = 'Invalid room number'
    
    if not data.get('category'):
        errors['category'] = 'Category is required'
    elif not isinstance(data['category'], str) or len(data['category']) > 50:
        errors['category'] = 'Invalid category'
    
    if not data.get('details'):
        errors['details'] = 'Details are required'
    
    if 'status' in data and data['status'] not in ['pending', 'resolved']:
        errors['status'] = 'Status must be pending or resolved'
    
    return errors

def validate_feedback_data(data):
    errors = {}
    if 'user_id' in data and data['user_id'] and not db.session.query(User).get(data['user_id']):
        errors['user_id'] = 'User not found'
    
    if not data.get('environment_rating'):
        errors['environment_rating'] = 'Environment rating is required'
    elif not isinstance(data['environment_rating'], str) or len(data['environment_rating']) > 20:
        errors['environment_rating'] = 'Invalid environment rating'
    
    if not data.get('service_rating'):
        errors['service_rating'] = 'Service rating is required'
    elif not isinstance(data['service_rating'], int) or data['service_rating'] < 1 or data['service_rating'] > 5:
        errors['service_rating'] = 'Service rating must be between 1 and 5'
    
    if not data.get('comments'):
        errors['comments'] = 'Comments are required'
    
    if not data.get('hostel'):
        errors['hostel'] = 'Hostel is required'
    elif not isinstance(data['hostel'], str) or len(data['hostel']) > 50:
        errors['hostel'] = 'Invalid hostel name'
    
    return errors

def validate_available_rooms_params(hostel_id, floor):
    errors = {}
    if not hostel_id:
        errors['hostel_id'] = 'Hostel ID is required'
    elif not isinstance(hostel_id, int) or not db.session.query(Hostel).get(hostel_id):
        errors['hostel_id'] = 'Invalid or non-existent hostel ID'
    
    if floor is None:
        errors['floor'] = 'Floor is required'
    elif not isinstance(floor, int) or floor < 0:
        errors['floor'] = 'Floor must be a non-negative integer'
    else:
        hostel = db.session.query(Hostel).get(hostel_id)
        if hostel and floor >= hostel.total_floors:
            errors['floor'] = f'Floor must be less than {hostel.total_floors}'
    
    return errors

# --- Models ---
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), nullable=True, unique=True)
    is_staff = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(100))
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
        
    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def role(self):
        if self.is_superuser:
            return "admin"
        elif self.is_staff:
            return "staff"
        else:
            return "user"
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "roll_number": self.roll_number,
            "is_staff": self.is_staff,
            "is_superuser": self.is_superuser,
            "role": self.role
        }

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    contact_number = db.Column(db.String(15))
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    user = db.relationship('User', backref='student_profile')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_number": self.contact_number,
            "profile_picture": self.profile_picture,
            "bio": self.bio,
        }

class Hostel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_floors = db.Column(db.Integer, nullable=False)
    main_image = db.Column(db.String(255))
    features = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "total_floors": self.total_floors,
            "main_image": self.main_image,
            "features": self.features,
        }

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostel.id'), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.String(10), nullable=False)
    ac_type = db.Column(db.String(10), nullable=False)
    total_beds = db.Column(db.Integer, nullable=False)
    occupied_beds = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    amenities = db.Column(db.Text)
    hostel = db.relationship('Hostel', backref='rooms')
    
    @property
    def beds_left(self):
        return self.total_beds - self.occupied_beds
    
    __table_args__ = (
        db.UniqueConstraint('hostel_id', 'room_number', name='unique_room_per_hostel'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "hostel_id": self.hostel_id,
            "floor": self.floor,
            "room_number": self.room_number,
            "room_type": self.room_type,
            "ac_type": self.ac_type,
            "total_beds": self.total_beds,
            "occupied_beds": self.occupied_beds,
            "price": str(self.price),
            "amenities": self.amenities,
        }

class Allocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref='allocations')
    room = db.relationship('Room', backref='allocations')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "allocation_date": self.allocation_date.strftime('%Y-%m-%d %H:%M:%S') if self.allocation_date else None,
            "status": self.status,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            "user": {
                "id": self.user.id,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email
            } if self.user else None,
            "room": {
                "id": self.room.id,
                "room_number": self.room.room_number,
                "room_type": self.room.room_type,
                "hostel": {
                    "id": self.room.hostel.id,
                    "name": self.room.hostel.name
                } if self.room and self.room.hostel else None
            } if self.room else None
        }

class RoomChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_allocation_id = db.Column(db.Integer, db.ForeignKey('allocation.id'), nullable=False)
    requested_room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref='room_change_requests')
    current_allocation = db.relationship('Allocation', backref='current_room_changes')
    requested_room = db.relationship('Room', backref='requested_room_changes')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "current_allocation_id": self.current_allocation_id,
            "requested_room_id": self.requested_room_id,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocation.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    status = db.Column(db.String(10), default='pending')
    receipt = db.Column(db.String(255))
    user = db.relationship('User', backref='payments')
    allocation = db.relationship('Allocation', backref='payments')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "allocation_id": self.allocation_id,
            "amount": str(self.amount),
            "payment_date": self.payment_date.strftime('%Y-%m-%d %H:%M:%S') if self.payment_date else None,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "receipt": self.receipt,
        }

class ComplaintMaintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='complaint_maintenance_requests')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "request_type": self.request_type,
            "room_number": self.room_number,
            "category": self.category,
            "details": self.details,
            "status": self.status,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    environment_rating = db.Column(db.String(20), nullable=False)
    service_rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)
    hostel = db.Column(db.String(50), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='feedbacks')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "environment_rating": self.environment_rating,
            "service_rating": self.service_rating,
            "comments": self.comments,
            "hostel": self.hostel,
            "submitted_at": self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None,
        }

# --- API Resources ---
class BaseResource(Resource):
    model = None

    def get(self, id=None):
        try:
            if id:
                instance = self.model.query.get_or_404(id)
                return instance.to_dict(), 200
            instances = self.model.query.all()
            return [instance.to_dict() for instance in instances], 200
        except Exception as e:
            return {"error": str(e)}, 500

    def delete(self, id):
        try:
            instance = self.model.query.get_or_404(id)
            db.session.delete(instance)
            db.session.commit()
            return {"message": f"{self.model.__name__} deleted"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class UserResource(BaseResource):
    model = User

    def post(self):
        try:
            data = request.get_json()
            errors = validate_user_data(data)
            if errors:
                return {"error": errors}, 400
            
            user = User(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                roll_number=data.get('roll_number'),
                is_staff=data.get('is_staff', False),
                is_superuser=data.get('is_superuser', False),
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.commit()
            return user.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            user = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_user_data(data, is_update=True, instance_id=id)
            if errors:
                return {"error": errors}, 400
            
            user.email = data.get('email', user.email)
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.roll_number = data.get('roll_number', user.roll_number)
            user.is_staff = data.get('is_staff', user.is_staff)
            user.is_superuser = data.get('is_superuser', user.is_superuser)
            if 'password' in data:
                user.set_password(data['password'])
            db.session.commit()
            return user.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class StudentProfileResource(BaseResource):
    model = StudentProfile

    def post(self):
        try:
            data = request.get_json()
            errors = validate_student_profile_data(data)
            if errors:
                return {"error": errors}, 400
            
            profile = StudentProfile(
                user_id=data['user_id'],
                contact_number=data.get('contact_number'),
                profile_picture=data.get('profile_picture'),
                bio=data.get('bio')
            )
            db.session.add(profile)
            db.session.commit()
            return profile.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            profile = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_student_profile_data(data)
            if errors:
                return {"error": errors}, 400
            
            profile.contact_number = data.get('contact_number', profile.contact_number)
            profile.profile_picture = data.get('profile_picture', profile.profile_picture)
            profile.bio = data.get('bio', profile.bio)
            db.session.commit()
            return profile.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class HostelResource(BaseResource):
    model = Hostel

    def post(self):
        try:
            data = request.get_json()
            errors = validate_hostel_data(data)
            if errors:
                return {"error": errors}, 400
            
            hostel = Hostel(
                name=data['name'],
                total_floors=data['total_floors'],
                main_image=data.get('main_image'),
                features=data.get('features')
            )
            db.session.add(hostel)
            db.session.commit()
            return hostel.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            hostel = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_hostel_data(data)
            if errors:
                return {"error": errors}, 400
            
            hostel.name = data.get('name', hostel.name)
            hostel.total_floors = data.get('total_floors', hostel.total_floors)
            hostel.main_image = data.get('main_image', hostel.main_image)
            hostel.features = data.get('features', hostel.features)
            db.session.commit()
            return hostel.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class RoomResource(BaseResource):
    model = Room

    def post(self):
        try:
            data = request.get_json()
            errors = validate_room_data(data)
            if errors:
                return {"error": errors}, 400
            
            room = Room(
                hostel_id=data['hostel_id'],
                floor=data['floor'],
                room_number=data['room_number'],
                room_type=data['room_type'],
                ac_type=data['ac_type'],
                total_beds=data['total_beds'],
                occupied_beds=data.get('occupied_beds', 0),
                price=data['price'],
                amenities=data.get('amenities')
            )
            db.session.add(room)
            db.session.commit()
            return room.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            room = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_room_data(data)
            if errors:
                return {"error": errors}, 400
            
            room.hostel_id = data.get('hostel_id', room.hostel_id)
            room.floor = data.get('floor', room.floor)
            room.room_number = data.get('room_number', room.room_number)
            room.room_type = data.get('room_type', room.room_type)
            room.ac_type = data.get('ac_type', room.ac_type)
            room.total_beds = data.get('total_beds', room.total_beds)
            room.occupied_beds = data.get('occupied_beds', room.occupied_beds)
            room.price = data.get('price', room.price)
            room.amenities = data.get('amenities', room.amenities)
            db.session.commit()
            return room.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class AllocationResource(BaseResource):
    model = Allocation

    def post(self):
        try:
            data = request.get_json()
            errors = validate_allocation_data(data)
            if errors:
                return {"error": errors}, 400
            
            alloc = Allocation(
                user_id=data['user_id'],
                room_id=data['room_id'],
                status=data.get('status', 'pending')
            )
            room = Room.query.get(data['room_id'])
            if not room or room.beds_left <= 0:
                return {"error": "Room not available"}, 400
            room.occupied_beds += 1
            db.session.add(alloc)
            db.session.commit()
            return alloc.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            alloc = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_allocation_data(data)
            if errors:
                return {"error": errors}, 400
            
            alloc.user_id = data.get('user_id', alloc.user_id)
            alloc.room_id = data.get('room_id', alloc.room_id)
            alloc.status = data.get('status', alloc.status)
            db.session.commit()
            return alloc.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class RoomChangeRequestResource(BaseResource):
    model = RoomChangeRequest

    def post(self):
        try:
            data = request.get_json()
            errors = validate_room_change_request_data(data)
            if errors:
                return {"error": errors}, 400
            
            req = RoomChangeRequest(
                user_id=data['user_id'],
                current_allocation_id=data['current_allocation_id'],
                requested_room_id=data['requested_room_id'],
                reason=data['reason'],
                status=data.get('status', 'pending')
            )
            db.session.add(req)
            db.session.commit()
            return req.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            req = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_room_change_request_data(data)
            if errors:
                return {"error": errors}, 400
            
            req.user_id = data.get('user_id', req.user_id)
            req.current_allocation_id = data.get('current_allocation_id', req.current_allocation_id)
            req.requested_room_id = data.get('requested_room_id', req.requested_room_id)
            req.reason = data.get('reason', req.reason)
            req.status = data.get('status', req.status)
            db.session.commit()
            return req.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class FeePaymentResource(BaseResource):
    model = FeePayment

    def post(self):
        try:
            data = request.get_json()
            errors = validate_fee_payment_data(data)
            if errors:
                return {"error": errors}, 400
            
            payment = FeePayment(
                user_id=data['user_id'],
                allocation_id=data['allocation_id'],
                amount=data['amount'],
                payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d %H:%M:%S') if data.get('payment_date') else datetime.utcnow(),
                transaction_id=data['transaction_id'],
                status=data.get('status', 'pending'),
                receipt=data.get('receipt')
            )
            db.session.add(payment)
            db.session.commit()
            return payment.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            payment = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_fee_payment_data(data)
            if errors:
                return {"error": errors}, 400
            
            payment.user_id = data.get('user_id', payment.user_id)
            payment.allocation_id = data.get('allocation_id', payment.allocation_id)
            payment.amount = data.get('amount', payment.amount)
            if 'payment_date' in data:
                payment.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d %H:%M:%S')
            payment.transaction_id = data.get('transaction_id', payment.transaction_id)
            payment.status = data.get('status', payment.status)
            payment.receipt = data.get('receipt', payment.receipt)
            db.session.commit()
            return payment.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class ComplaintMaintenanceResource(BaseResource):
    model = ComplaintMaintenance

    def post(self):
        try:
            data = request.get_json()
            errors = validate_complaint_maintenance_data(data)
            if errors:
                return {"error": errors}, 400
            
            complaint = ComplaintMaintenance(
                user_id=data['user_id'],
                request_type=data['request_type'],
                room_number=data['room_number'],
                category=data['category'],
                details=data['details'],
                status=data.get('status', 'pending')
            )
            db.session.add(complaint)
            db.session.commit()
            return complaint.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            complaint = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_complaint_maintenance_data(data)
            if errors:
                return {"error": errors}, 400
            
            complaint.user_id = data.get('user_id', complaint.user_id)
            complaint.request_type = data.get('request_type', complaint.request_type)
            complaint.room_number = data.get('room_number', complaint.room_number)
            complaint.category = data.get('category', complaint.category)
            complaint.details = data.get('details', complaint.details)
            complaint.status = data.get('status', complaint.status)
            db.session.commit()
            return complaint.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class FeedbackResource(BaseResource):
    model = Feedback

    def post(self):
        try:
            data = request.get_json()
            errors = validate_feedback_data(data)
            if errors:
                return {"error": errors}, 400
            
            feedback = Feedback(
                user_id=data.get('user_id'),
                environment_rating=data['environment_rating'],
                service_rating=data['service_rating'],
                comments=data['comments'],
                hostel=data['hostel'],
                submitted_at=datetime.strptime(data['submitted_at'], '%Y-%m-%d %H:%M:%S') if data.get('submitted_at') else datetime.utcnow()
            )
            db.session.add(feedback)
            db.session.commit()
            return feedback.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            feedback = self.model.query.get_or_404(id)
            data = request.get_json()
            errors = validate_feedback_data(data)
            if errors:
                return {"error": errors}, 400
            
            feedback.user_id = data.get('user_id', feedback.user_id)
            feedback.environment_rating = data.get('environment_rating', feedback.environment_rating)
            feedback.service_rating = data.get('service_rating', feedback.service_rating)
            feedback.comments = data.get('comments', feedback.comments)
            feedback.hostel = data.get('hostel', feedback.hostel)
            if 'submitted_at' in data:
                feedback.submitted_at = datetime.strptime(data['submitted_at'], '%Y-%m-%d %H:%M:%S')
            db.session.commit()
            return feedback.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class AvailableRoomsResource(Resource):
    def get(self):
        try:
            hostel_id = request.args.get('hostel_id', type=int)
            floor = request.args.get('floor', type=int)
            errors = validate_available_rooms_params(hostel_id, floor)
            if errors:
                return {"error": errors}, 400

            available = {"four": [], "double": [], "single": []}
            booked = []
            rooms = Room.query.filter_by(hostel_id=hostel_id, floor=floor).all()
            for room in rooms:
                room_type = room.room_type
                if room.beds_left > 0:
                    available[room_type].append({
                        "number": room.room_number,
                        "beds_left": room.beds_left,
                        "id": room.id,
                        "ac_type": room.ac_type,
                        "price": str(room.price),
                        "amenities": room.amenities
                    })
                else:
                    booked.append(room.room_number)
            return {
                "available": available,
                "booked": booked,
                "hostel": hostel_id,
                "floor": floor
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500

class RoomAllocationResource(Resource):
    @login_required
    def post(self):
        try:
            if current_user.is_superuser:
                return {"success": False, "message": "Admins cannot allocate rooms."}, 400

            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = {
                    'hostel_id': request.form.get('hostel'),
                    'floor': request.form.get('floor'),
                    'room_number': request.form.get('room_number'),
                    'room_type': request.form.get('room-type')
                }

            # Convert and validate inputs
            try:
                data['hostel_id'] = int(data['hostel_id'])
                data['floor'] = int(data['floor'])
            except (ValueError, TypeError):
                return {"success": False, "message": "Invalid hostel_id or floor"}, 400

            errors = validate_room_allocation_data(data)
            if errors:
                return {"success": False, "message": errors}, 400

            hostel_obj = Hostel.query.get(data['hostel_id'])
            if not hostel_obj:
                return {"success": False, "message": "Hostel not found!"}, 404

            room = Room.query.filter_by(
                room_number=data['room_number'],
                hostel_id=data['hostel_id'],
                floor=data['floor'],
                room_type=data['room_type']
            ).first()
            if not room:
                return {"success": False, "message": "Room not found!"}, 404

            if room.beds_left <= 0:
                return {"success": False, "message": "Room not available!"}, 400

            existing_allocation = Allocation.query.filter_by(user_id=current_user.id).first()
            if existing_allocation:
                return {"success": False, "message": "You have already booked a room!"}, 400

            allocation = Allocation(
                user_id=current_user.id,
                room_id=room.id,
                status='allocated'
            )
            room.occupied_beds += 1
            db.session.add(allocation)
            db.session.commit()
            return {"success": True, "message": "Room allocated successfully!"}, 201
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Error: {str(e)}"}, 500

# --- API Routes ---
api.add_resource(UserResource, '/api/v1/users', '/api/v1/users/<int:id>')
api.add_resource(StudentProfileResource, '/api/v1/student_profiles', '/api/v1/student_profiles/<int:id>')
api.add_resource(HostelResource, '/api/v1/hostels', '/api/v1/hostels/<int:id>')
api.add_resource(RoomResource, '/api/v1/rooms', '/api/v1/rooms/<int:id>')
api.add_resource(AllocationResource, '/api/v1/allocations', '/api/v1/allocations/<int:id>')
api.add_resource(RoomChangeRequestResource, '/api/v1/room_change_requests', '/api/v1/room_change_requests/<int:id>')
api.add_resource(FeePaymentResource, '/api/v1/fee_payments', '/api/v1/fee_payments/<int:id>')
api.add_resource(ComplaintMaintenanceResource, '/api/v1/complaints', '/api/v1/complaints/<int:id>')
api.add_resource(FeedbackResource, '/api/v1/feedbacks', '/api/v1/feedbacks/<int:id>')
api.add_resource(AvailableRoomsResource, '/api/v1/available_rooms')
api.add_resource(RoomAllocationResource, '/api/v1/room_allocation')

# --- Legacy API Route for Django Compatibility ---
@app.route('/api/get_available_rooms', methods=['GET'])
def get_available_rooms():
    try:
        hostel_id = request.args.get('hostel_id', type=int)
        floor = request.args.get('floor', type=int)
        errors = validate_available_rooms_params(hostel_id, floor)
        if errors:
            return jsonify({"error": errors}), 400

        available = {"four": [], "double": [], "single": []}
        booked = []
        rooms = Room.query.filter_by(hostel_id=hostel_id, floor=floor).all()
        for room in rooms:
            room_type = room.room_type
            if room.beds_left > 0:
                available[room_type].append({
                    "number": room.room_number,
                    "beds_left": room.beds_left,
                    "id": room.id,
                    "ac_type": room.ac_type,
                    "price": str(room.price),
                    "amenities": room.amenities
                })
            else:
                booked.append(room.room_number)
        return jsonify({
            "available": available,
            "booked": booked,
            "hostel": hostel_id,
            "floor": floor
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Non-API Routes ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if admin_user is None:
        admin_user = User(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True
        )
        admin_user.set_password("password123")
        db.session.add(admin_user)
        db.session.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/room_allocation', methods=['GET', 'POST'])
@login_required
def room_allocation():
    if request.method == 'POST':
        if current_user.is_superuser:
            return jsonify({"success": False, "message": "Admins cannot allocate rooms."}), 400
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = {
                    'hostel_id': request.form.get('hostel'),
                    'floor': request.form.get('floor'),
                    'room_number': request.form.get('room_number'),
                    'room_type': request.form.get('room-type')
                }
            
            # Convert and validate inputs
            try:
                data['hostel_id'] = int(data['hostel_id'])
                data['floor'] = int(data['floor'])
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Invalid hostel_id or floor"}), 400

            errors = validate_room_allocation_data(data)
            if errors:
                return jsonify({"success": False, "message": errors}), 400

            hostel_obj = Hostel.query.get(data['hostel_id'])
            if not hostel_obj:
                return jsonify({'message': 'Hostel not found!', 'success': False}), 404

            room = Room.query.filter_by(
                room_number=data['room_number'],
                hostel_id=data['hostel_id'],
                floor=data['floor'],
                room_type=data['room_type']
            ).first()
            if not room:
                return jsonify({'message': 'Room not found!', 'success': False}), 404

            if room.beds_left <= 0:
                return jsonify({'message': 'Room not available!', 'success': False}), 400

            existing_allocation = Allocation.query.filter_by(user_id=current_user.id).first()
            if existing_allocation:
                return jsonify({'message': 'You have already booked a room!', 'success': False}), 400

            allocation = Allocation(
                user_id=current_user.id,
                room_id=room.id,
                status='allocated'
            )
            room.occupied_beds += 1
            db.session.add(allocation)
            db.session.commit()
            return jsonify({'message': 'Room allocated successfully!', 'success': True}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Error: {str(e)}', 'success': False}), 500

    hostels = Hostel.query.all()
    hostels_data = [
        {
            "id": h.id,
            "name": h.name,
            "total_floors": h.total_floors,
            "features": h.features,
            "main_image": h.main_image
        }
        for h in hostels
    ]
    return render_template('room_allocation.html', hostels=hostels_data)

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        try:
            data = {
                'environment_rating': request.form.get('environment_rating'),
                'service_rating': int(request.form.get('service_rating')),
                'comments': request.form.get('comments'),
                'hostel': request.form.get('hostel'),
                'user_id': current_user.id
            }
            errors = validate_feedback_data(data)
            if errors:
                flash(f'Validation error: {errors}', 'error')
                return redirect(url_for('feedback'))

            new_feedback = Feedback(**data)
            db.session.add(new_feedback)
            db.session.commit()
            flash('Feedback submitted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting feedback: {str(e)}', 'error')

    feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()
    hostels = Hostel.query.all()
    return render_template('feedback.html', feedbacks=feedbacks, hostels=hostels)

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/hostel_details')
def hostel_details():
    return render_template('hostel_details.html')

@app.route('/about')
def about():
    feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()
    return render_template('about.html', feedbacks=feedbacks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if (role == "admin" and user.is_superuser) or (role == "user" and not user.is_superuser):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for("dashboard" if user.is_superuser else "home"))
            flash("Invalid role selected!", "danger")
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'roll_number': request.form.get('roll_number')
            }
            if request.form.get('password') != request.form.get('confirm_password'):
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('signup'))

            errors = validate_user_data(data)
            if errors:
                flash(f'Validation error: {errors}', 'danger')
                return redirect(url_for('signup'))

            new_user = User(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                roll_number=data['roll_number']
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('signup.html')

@app.route('/profile')
@login_required
def profile():
    user = current_user
    allocation = Allocation.query.filter_by(user_id=user.id).first()
    hostel = allocation.room.hostel if allocation else None
    return render_template('profile.html', user=user, allocation=allocation, hostel=hostel)

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_superuser:
        return redirect(url_for('home'))

    search_query = request.args.get('search', '')
    users = User.query.filter(
        db.or_(
            User.first_name.contains(search_query),
            User.last_name.contains(search_query),
            User.email.contains(search_query)
        )
    ).all() if search_query else User.query.all()

    return render_template('dashboard.html',
                           users=users,
                           rooms_count=Room.query.count(),
                           pending_requests=ComplaintMaintenance.query.filter_by(status='pending').count(),
                           feedback_count=Feedback.query.count(),
                           feedbacks=Feedback.query.order_by(Feedback.submitted_at.desc()).all(),
                           active_tab='users',
                           search_query=search_query)

@app.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
    try:
        data = {
            'request_type': request.form.get('request_type'),
            'category': request.form.get('maintenance_type') or request.form.get('complaint_type'),
            'user_id': current_user.id,
            'room_number': request.form.get('room_number'),
            'details': request.form.get('details'),
            'status': 'pending'
        }
        errors = validate_complaint_maintenance_data(data)
        if errors:
            flash(f'Validation error: {errors}', 'error')
            return redirect(url_for('complaint_and_maintenance'))

        req = ComplaintMaintenance(**data)
        db.session.add(req)
        db.session.commit()
        flash('Request submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'error')
    
    return redirect(url_for('complaint_and_maintenance'))

@app.route('/complaint_and_maintenance')
@login_required
def complaint_and_maintenance():
    maintenance_requests = ComplaintMaintenance.query.filter_by(
        user_id=current_user.id, 
        request_type='maintenance'
    ).order_by(ComplaintMaintenance.created_at.desc()).limit(5).all()
    
    complaints = ComplaintMaintenance.query.filter_by(
        user_id=current_user.id, 
        request_type='complaint'
    ).order_by(ComplaintMaintenance.created_at.desc()).limit(5).all()
    
    return render_template(
        'complaint_and_maintenance.html',
        maintenance_requests=maintenance_requests,
        complaints=complaints
    )

@app.route('/view_requests')
@login_required
def view_requests():
    if not current_user.is_superuser:
        return redirect(url_for('home'))
    
    requests = ComplaintMaintenance.query.order_by(ComplaintMaintenance.created_at.desc()).all()
    return render_template('dashboard.html',
                           users=User.query.all(),
                           feedback_count=Feedback.query.count(),
                           requests=requests,
                           pending_requests=ComplaintMaintenance.query.filter_by(status='pending').count(),
                           active_tab='requests',
                           rooms_count=Room.query.count())

@app.route('/view_feedback')
@login_required
def view_feedback():
    if not current_user.is_superuser:
        return redirect(url_for('home'))
    return render_template('dashboard.html',
                           users=User.query.all(),
                           rooms_count=Room.query.count(),
                           pending_requests=ComplaintMaintenance.query.filter_by(status='pending').count(),
                           feedback_count=Feedback.query.count(),
                           feedbacks=Feedback.query.order_by(Feedback.submitted_at.desc()).all(),
                           active_tab='feedback')

@app.route('/view_allocations')
@login_required
def view_allocations():
    if not current_user.is_superuser:
        return redirect(url_for('home'))

    search_query = request.args.get('search', '')
    users = User.query.filter(
        db.or_(
            User.first_name.contains(search_query),
            User.last_name.contains(search_query),
            User.email.contains(search_query)
        )
    ).all() if search_query else User.query.all()

    return render_template(
        'dashboard.html',
        users=users,
        rooms_count=Room.query.count(),
        allocations=Allocation.query.all(),
        active_tab='allocations'
    )

@app.route('/edit_room_allocation/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_room_allocation(id):
    if not current_user.is_superuser:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    alloc = Allocation.query.get_or_404(id)
    if request.method == 'POST':
        try:
            data = {
                'room_id': request.form.get('room_id'),
                'status': request.form.get('status'),
                'user_id': alloc.user_id
            }
            errors = validate_allocation_data(data)
            if errors:
                flash(f'Validation error: {errors}', 'error')
                return redirect(url_for('edit_room_allocation', id=id))

            alloc.room_id = data['room_id']
            alloc.status = data['status']
            db.session.commit()
            flash('Room allocation updated!', 'success')
            return redirect(url_for('view_allocations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    rooms = Room.query.all()
    return render_template('edit_room_allocation.html', allocation=alloc, rooms=rooms)

@app.route("/api/routes", methods=["GET"])
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(rule.methods)
            url = urllib.parse.unquote(str(rule))
            output.append({"endpoint": rule.endpoint, "methods": methods, "url": url})
    return jsonify(sorted(output, key=lambda x: x["url"]))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)