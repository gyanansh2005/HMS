from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import InternalServerError
from flask_cors import CORS
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config['SECRET_KEY'] = 'my_secret_key'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    username = db.Column(db.String(100), nullable=False, unique=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class RoomAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(10), nullable=False)
    beds_left = db.Column(db.Integer, nullable=False, default=4)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    student_roll_no = db.Column(db.String(20), nullable=False, unique=True)
    __table_args__ = (
        db.UniqueConstraint('hostel', 'floor', 'room_number', 'user_id', name='uq_hostel_floor_room_user'),
    )

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    maintenance_type = db.Column(db.String(50))
    complaint_type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='requests')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    environment = db.Column(db.String(20), nullable=False)
    service_rating = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    hostel = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ensure the database and tables are created
with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user is None:
        admin_user = User(
            name="Admin",
            email="admin@example.com",
            username="admin",
            role="admin"
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
        try:
            hostel = request.form['hostel']
            floor = int(request.form['floor'])
            room_number = int(request.form['room-number'])
            room_type = request.form['room-type']
            student_name = request.form['student-name']
            student_roll_no = int(request.form['student-roll-no'])

            print("Received data:", {
                "hostel": hostel,
                "floor": floor,
                "room_number": room_number,
                "room_type": room_type,
                "student_name": student_name,
                "student_roll": student_roll_no,
            })
            existing_allocation = RoomAllocation.query.filter_by(student_roll_no=student_roll_no).first()
            if existing_allocation:
                return jsonify({'message': 'You have already booked a room!', 'success': False})

            room = RoomAllocation.query.filter_by(room_number=room_number).first()

            if not room:
                beds_left = 4 if room_type == "four" else (2 if room_type == "double" else 1)
                room = RoomAllocation(
                    hostel=hostel,
                    floor=floor,
                    room_number=room_number,
                    room_type=room_type,
                    beds_left=beds_left - 1,
                    user_id=current_user.id,
                    student_name=student_name,
                    student_roll_no=student_roll_no
                )
                db.session.add(room)
                db.session.commit()
                print("Room created successfully!")
                return jsonify({'message': 'Room allocated successfully!', 'success': True})
            
            elif room.beds_left > 0:
                room.beds_left -= 1
                room.student_name = student_name
                room.user_id = current_user.id
                db.session.commit()
                print("Room allocated successfully!")
                return jsonify({'message': 'Room allocated successfully!', 'success': True})
            
            else:
                print("Room is full!")
                return jsonify({'message': 'Room not available!', 'success': False})

        except Exception as e:
            print("Error:", str(e))
            return jsonify({'message': f'Internal Server Error: {str(e)}', 'success': False}), 500

    return render_template('room_allocation.html')

@app.route('/get_available_rooms', methods=['GET'])
def get_available_rooms():
    selected_hostel = request.args.get('hostel', default='hostel-1')
    selected_floor = int(request.args.get('floor', default=1))

    base_room = {
        "hostel-1": 0,
        "hostel-2": 0,
        "hostel-3": 0,
        "hostel-4": 0,
    }
    room_offset = base_room.get(selected_hostel, 100)
    room_start = room_offset + (selected_floor * 100)
    predefined_rooms = {
        "four": list(range(room_start + 1, room_start + 17)),
        "double": list(range(room_start + 17, room_start + 25)),
        "single": list(range(room_start + 25, room_start + 35)),
    }

    available = {"four": [], "double": [], "single": []}
    booked = []

    for room_type, numbers in predefined_rooms.items():
        max_beds = 4 if room_type == 'four' else 2 if room_type == 'double' else 1
        for number in numbers:
            count = RoomAllocation.query.filter_by(
                hostel=selected_hostel,
                floor=selected_floor,
                room_number=number,
                room_type=room_type
            ).count()
            beds_left = max_beds - count
            if beds_left > 0:
                available[room_type].append({'number': number, 'beds_left': beds_left})
            else:
                booked.append(number)
    return jsonify({"available": available, "booked": booked})

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/get_requests', methods=['GET'])
@login_required
def get_requests():
    requests = Request.query.order_by(Request.created_at.desc()).all()
    return jsonify([{'id': request.id, 'type': request.type, 'user': request.user.name, 'room_number': request.room_number, 'details': request.details, 'status': request.status} for request in requests])

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        try:
            new_feedback = Feedback(
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                email=request.form['email'],
                environment=request.form['environment'],
                service_rating=request.form['service_rating'],
                description=request.form['descr'],
                hostel=request.form['hostel']
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash('Feedback submitted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error submitting feedback', 'error')
    
    all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('feedback.html', feedbacks=all_feedback)

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/hostel_details')
def hostel_details():
    return render_template('hostel_details.html')

@app.route('/about')
def about():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('about.html', feedbacks=feedbacks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        print("Role selected in form:", role)
        print("Email entered:", email)

        user = User.query.filter_by(email=email, role=role).first()
        print("Query:", User.query.filter_by(email=email, role=role))

        if user and user.check_password(password):
            login_user(user)
            session['username'] = user.name
            flash("Login successful!", "success")
            if user.role == "admin":
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("home"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('login'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('login'))
        new_user = User(name=name, email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template('signup.html')

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(current_user.id)
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/get_user/<int:user_id>')
@login_required
def get_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'username': user.username,
        'role': user.role
    })

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query) | User.email.contains(search_query)).all() if search_query else User.query.all()
    
    return render_template('dashboard.html',
                           users=users,
                           rooms_count=RoomAllocation.query.count(),
                           pending_requests=Request.query.filter_by(status='pending').count(),
                           feedback_count=Feedback.query.count(),
                           active_tab='users',
                           search_query=search_query)

@app.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
    try:
        request_type = request.form.get('request_type')
        req = Request(
            type=request_type,
            maintenance_type=request.form.get('maintenance_type'),
            complaint_type=request.form.get('complaint_type'),
            user_id=current_user.id,
            room_number=request.form.get('room_number'),
            details=request.form.get('details'),
            status='pending'
        )
        
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
    maintenance_requests = Request.query.filter_by(
        user_id=current_user.id, 
        type='maintenance'
    ).order_by(Request.created_at.desc()).limit(5).all()
    
    complaints = Request.query.filter_by(
        user_id=current_user.id, 
        type='complaint'
    ).order_by(Request.created_at.desc()).limit(5).all()
    
    return render_template(
        'complaint_and_maintenance.html',
        maintenance_requests=maintenance_requests,
        complaints=complaints
    )

@app.route('/view_requests')
@login_required
def view_requests():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    requests = Request.query.order_by(Request.created_at.desc()).all()
    pending_requests = Request.query.filter_by(status='pending').count()
    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query) | User.email.contains(search_query)).all() if search_query else User.query.all()
    
    return render_template('dashboard.html',
                           users=users,
                           rooms_count=RoomAllocation.query.count(),
                           feedback_count=Feedback.query.count(),
                           requests=requests,
                           pending_requests=pending_requests,
                           active_tab='requests')

@app.route('/view_feedback')
@login_required
def view_feedback():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query) | User.email.contains(search_query)).all() if search_query else User.query.all()
    
    return render_template('dashboard.html',
                           users=users,
                           rooms_count=RoomAllocation.query.count(),
                           pending_requests=Request.query.filter_by(status='pending').count(),
                           feedback_count=Feedback.query.count(),
                           feedbacks=Feedback.query.order_by(Feedback.created_at.desc()).all(),
                           active_tab='feedback')

@app.route('/view_allocations')
@login_required
def view_allocations():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query) | User.email.contains(search_query)).all() if search_query else User.query.all()
    
    return render_template('dashboard.html',
                           users=users,
                           rooms_count=RoomAllocation.query.count(),
                           pending_requests=Request.query.filter_by(status='pending').count(),
                           feedback_count=Feedback.query.count(),
                           allocations=RoomAllocation.query.order_by(RoomAllocation.hostel, RoomAllocation.floor).all(),
                           active_tab='allocations')

@app.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        role = request.form.get('role')

        # Validate input
        if not all([name, email, username, role]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('dashboard'))

        # Check for duplicate email (excluding the current user)
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            flash('Email already exists!', 'danger')
            return redirect(url_for('dashboard'))

        # Check for duplicate username (excluding the current user)
        existing_username = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_username:
            flash('Username already exists!', 'danger')
            return redirect(url_for('dashboard'))

        # Update user
        user.name = name
        user.email = email
        user.username = username
        user.role = role
        db.session.commit()
        flash('User updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/update_request/<int:request_id>/<status>')
@login_required
def update_request(request_id, status):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    request = Request.query.get_or_404(request_id)
    try:
        request.status = status
        db.session.commit()
        flash(f'Request marked as {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating request: {str(e)}', 'danger')
    return redirect(url_for('view_requests'))

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Check for associated records and delete them
        RoomAllocation.query.filter_by(user_id=user_id).delete()
        Request.query.filter_by(user_id=user_id).delete()
        Feedback.query.filter_by(email=user.email).delete()

        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User and associated records deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('dashboard'))

# ROOM ALLOCATION API
@app.route('/api/room_allocations', methods=['GET'])
def get_room_allocations():
    allocations = RoomAllocation.query.all()
    result = []
    for alloc in allocations:
        result.append({
            'id': alloc.id,
            'hostel': alloc.hostel,
            'floor': alloc.floor,
            'room_number': alloc.room_number,
            'room_type': alloc.room_type,
            'beds_left': alloc.beds_left,
            'user_id': alloc.user_id,
            'student_name': alloc.student_name,
            'student_roll_no': alloc.student_roll_no
        })
    return jsonify(result)

@app.route('/api/room_allocations/<int:id>', methods=['GET'])
def get_room_allocation(id):
    alloc = RoomAllocation.query.get_or_404(id)
    return jsonify({
        'id': alloc.id,
        'hostel': alloc.hostel,
        'floor': alloc.floor,
        'room_number': alloc.room_number,
        'room_type': alloc.room_type,
        'beds_left': alloc.beds_left,
        'user_id': alloc.user_id,
        'student_name': alloc.student_name,
        'student_roll_no': alloc.student_roll_no
    })

@app.route('/api/room_allocations', methods=['POST'])
def create_room_allocation():
    data = request.json
    alloc = RoomAllocation(
        hostel=data['hostel'],
        floor=data['floor'],
        room_number=data['room_number'],
        room_type=data['room_type'],
        beds_left=data.get('beds_left', 4),
        user_id=data['user_id'],
        student_name=data['student_name'],
        student_roll_no=data['student_roll_no']
    )
    db.session.add(alloc)
    db.session.commit()
    return jsonify({'message': 'Room allocation created', 'id': alloc.id}), 201

@app.route('/api/room_allocations/<int:id>', methods=['PUT'])
def update_room_allocation(id):
    alloc = RoomAllocation.query.get_or_404(id)
    data = request.json
    alloc.hostel = data.get('hostel', alloc.hostel)
    alloc.floor = data.get('floor', alloc.floor)
    alloc.room_number = data.get('room_number', alloc.room_number)
    alloc.room_type = data.get('room_type', alloc.room_type)
    alloc.beds_left = data.get('beds_left', alloc.beds_left)
    alloc.user_id = data.get('user_id', alloc.user_id)
    alloc.student_name = data.get('student_name', alloc.student_name)
    alloc.student_roll_no = data.get('student_roll_no', alloc.student_roll_no)
    db.session.commit()
    return jsonify({'message': 'Room allocation updated'})

@app.route('/api/room_allocations/<int:id>', methods=['DELETE'])
def delete_room_allocation(id):
    alloc = RoomAllocation.query.get_or_404(id)
    db.session.delete(alloc)
    db.session.commit()
    return jsonify({'message': 'Room allocation deleted'})

# REQUEST API
@app.route('/api/requests', methods=['GET'])
def get_requests_api():
    requests_list = Request.query.all()
    result = []
    for req in requests_list:
        result.append({
            'id': req.id,
            'type': req.type,
            'maintenance_type': req.maintenance_type,
            'complaint_type': req.complaint_type,
            'user_id': req.user_id,
            'room_number': req.room_number,
            'details': req.details,
            'status': req.status,
            'created_at': req.created_at
        })
    return jsonify(result)

@app.route('/api/requests/<int:id>', methods=['GET'])
def get_request_api(id):
    req = Request.query.get_or_404(id)
    return jsonify({
        'id': req.id,
        'type': req.type,
        'maintenance_type': req.maintenance_type,
        'complaint_type': req.complaint_type,
        'user_id': req.user_id,
        'room_number': req.room_number,
        'details': req.details,
        'status': req.status,
        'created_at': req.created_at
    })

@app.route('/api/requests', methods=['POST'])
def create_request():
    data = request.json
    req = Request(
        type=data['type'],
        maintenance_type=data.get('maintenance_type'),
        complaint_type=data.get('complaint_type'),
        user_id=data['user_id'],
        room_number=data['room_number'],
        details=data['details'],
        status=data.get('status', 'pending')
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({'message': 'Request created', 'id': req.id}), 201

@app.route('/api/requests/<int:id>', methods=['PUT'])
def update_request_api(id):
    req = Request.query.get_or_404(id)
    data = request.json
    req.type = data.get('type', req.type)
    req.maintenance_type = data.get('maintenance_type', req.maintenance_type)
    req.complaint_type = data.get('complaint_type', req.complaint_type)
    req.user_id = data.get('user_id', req.user_id)
    req.room_number = data.get('room_number', req.room_number)
    req.details = data.get('details', req.details)
    req.status = data.get('status', req.status)
    db.session.commit()
    return jsonify({'message': 'Request updated'})

@app.route('/api/requests/<int:id>', methods=['DELETE'])
def delete_request_api(id):
    req = Request.query.get_or_404(id)
    db.session.delete(req)
    db.session.commit()
    return jsonify({'message': 'Request deleted'})

# USERS API
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'username': user.username,
            'role': user.role
        })
    return jsonify(result)

@app.route('/api/users/<int:id>', methods=['GET'])
def get_user_api(id):
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'username': user.username,
        'role': user.role
    })

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user_api(id):
    try:
        user = User.query.get_or_404(id)
        # Check if user has any room allocations
        allocations = RoomAllocation.query.filter_by(user_id=id).all()
        if allocations:
            return jsonify({
                'message': 'Cannot delete user with active room allocations'
            }), 400
        # Check if user has any requests
        requests = Request.query.filter_by(user_id=id).all()
        if requests:
            return jsonify({
                'message': 'Cannot delete user with active requests'
            }), 400
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Error deleting user: {str(e)}'
        }), 500

# FEEDBACKS API
@app.route('/api/feedbacks', methods=['GET'])
def get_feedbacks():
    feedbacks = Feedback.query.all()
    result = []
    for fb in feedbacks:
        result.append({
            'id': fb.id,
            'first_name': fb.first_name,
            'last_name': fb.last_name,
            'email': fb.email,
            'environment': fb.environment,
            'service_rating': fb.service_rating,
            'description': fb.description,
            'hostel': fb.hostel,
            'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result)

@app.route('/api/feedbacks/<int:id>', methods=['GET'])
def get_feedback(id):
    fb = Feedback.query.get_or_404(id)
    return jsonify({
        'id': fb.id,
        'first_name': fb.first_name,
        'last_name': fb.last_name,
        'email': fb.email,
        'environment': fb.environment,
        'service_rating': fb.service_rating,
        'description': fb.description,
        'hostel': fb.hostel,
        'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/feedbacks/<int:id>', methods=['DELETE'])
def delete_feedback_api(id):
    try:
        feedback = Feedback.query.get_or_404(id)
        db.session.delete(feedback)
        db.session.commit()
        return jsonify({'message': 'Feedback deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Error deleting feedback: {str(e)}'
        }), 500

@app.route('/api/get_available_rooms', methods=['GET'])
def get_available_rooms_api():
    try:
        selected_hostel = request.args.get('hostel', default='hostel-1')
        selected_floor = int(request.args.get('floor', default=1))
        
        print(f"Fetching rooms for hostel: {selected_hostel}, floor: {selected_floor}")  # Debug print
        
        # Get existing room allocations for this floor
        existing_rooms = RoomAllocation.query.filter_by(
            hostel=selected_hostel,
            floor=selected_floor
        ).all()
        
        print(f"Found {len(existing_rooms)} existing rooms")  # Debug print
        
        # Create a dictionary of allocated rooms for quick lookup
        allocated_rooms = {}
        for room in existing_rooms:
            key = f"{room.room_number}_{room.room_type}"
            allocated_rooms[key] = room
        
        # Define room ranges for different types
        base_room = {
            "hostel-1": 0,
            "hostel-2": 100,
            "hostel-3": 200,
            "hostel-4": 300,
        }
        room_offset = base_room.get(selected_hostel, 0)
        room_start = room_offset + (selected_floor * 100)
        
        predefined_rooms = {
            "four": list(range(room_start + 1, room_start + 17)),
            "double": list(range(room_start + 17, room_start + 25)),
            "single": list(range(room_start + 25, room_start + 35)),
        }
        
        available = {"four": [], "double": [], "single": []}
        booked = []
        
        # Process each room type
        for room_type, numbers in predefined_rooms.items():
            max_beds = 4 if room_type == 'four' else 2 if room_type == 'double' else 1
            for number in numbers:
                key = f"{number}_{room_type}"
                room = allocated_rooms.get(key)
                
                if room:
                    print(f"Room {number} ({room_type}): {room.beds_left} beds left")  # Debug print
                    if room.beds_left > 0:
                        available[room_type].append({
                            'number': number,
                            'beds_left': room.beds_left,
                            'student_name': room.student_name,
                            'student_roll_no': room.student_roll_no
                        })
                    else:
                        booked.append({
                            'number': number,
                            'type': room_type,
                            'student_name': room.student_name,
                            'student_roll_no': room.student_roll_no
                        })
                else:
                    available[room_type].append({
                        'number': number,
                        'beds_left': max_beds
                    })
        
        print(f"Available rooms: {available}")  # Debug print
        print(f"Booked rooms: {booked}")  # Debug print
        
        return jsonify({
            "available": available,
            "booked": booked,
            "hostel": selected_hostel,
            "floor": selected_floor
        })
        
    except Exception as e:
        print(f"Error in get_available_rooms_api: {str(e)}")  # Debug print
        return jsonify({
            "error": str(e),
            "available": {"four": [], "double": [], "single": []},
            "booked": [],
            "hostel": selected_hostel,
            "floor": selected_floor
        }), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)