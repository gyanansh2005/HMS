from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import InternalServerError
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user



basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
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
    beds_left = db.Column(db.Integer, nullable=False, default=4)  # Added beds_left column
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_name = db.Column(db.String(50), nullable=False)
    student_roll_no = db.Column(db.String(20), nullable=False, unique=True)  
    __table_args__ = (
        db.UniqueConstraint('hostel', 'floor', 'room_number', 'user_id', name='uq_hostel_floor_room_user'),
    )
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'maintenance' or 'complaint'
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


            # Check if the room already exists
            room = RoomAllocation.query.filter_by(room_number=room_number).first()

            if not room:
                # If the room doesn't exist, create it
                beds_left = 4 if room_type == "four" else (2 if room_type == "double" else 1)
                room = RoomAllocation(
                    hostel=hostel, 
                    floor=floor, 
                    room_number=room_number,
                    room_type=room_type, 
                    beds_left=beds_left - 1, 
                    user_id=current_user.id,  # Set the user_id to the current user's ID
                    student_name=student_name,
                    student_roll_no=student_roll_no
                )
                db.session.add(room)
                db.session.commit()
                print("Room created successfully!")
                return jsonify({'message': 'Room allocated successfully!', 'success': True})
            
            elif room.beds_left > 0:
                # If the room exists and has beds left, allocate it
                room.beds_left -= 1
                room.student_name = student_name
                room.user_id = current_user.id  # Set the user_id to the current user's ID
                db.session.commit()
                print("Room allocated successfully!")
                return jsonify({'message': 'Room allocated successfully!', 'success': True})
            
            else:
                # If the room is full
                print("Room is full!")
                return jsonify({'message': 'Room not available!', 'success': False})

        except Exception as e:
            print("Error:", str(e))
            return jsonify({'message': f'Internal Server Error: {str(e)}', 'success': False}), 500

    return render_template('room_allocation.html')

@app.route('/get_available_rooms', methods=['GET'])
def get_available_rooms():
    # Get selected hostel and floor from the request
    selected_hostel = request.args.get('hostel', default='hostel-1')
    selected_floor = int(request.args.get('floor', default=1))

    # Define room numbers based on hostel and floor
    base_room = {
        "hostel-1": 0,
        "hostel-2": 0,
        "hostel-3": 0,
        "hostel-4": 0,
    }
    room_offset = base_room.get(selected_hostel, 100)  # Default to hostel-1 if invalid
    room_start = room_offset + (selected_floor * 100)  # Example: hostel-1, floor 2 → 100 + 200 = 300
    predefined_rooms = {
        "four": list(range(room_start + 1, room_start + 17)),          
        "double": list(range(room_start + 17, room_start + 25)),
        "single": list(range(room_start + 25, room_start + 35)) ,
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
            session['username'] = user.name  # Store username in session
            flash("Login successful!", "success")
            if user.role == "admin":
                return redirect(url_for("dashboard"))  # Redirect admin to dashboard
            else:
                return redirect(url_for("home"))  # Redirect normal users to home
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

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     if current_user.role != 'admin':
#         return redirect(url_for('home'))
#     users = User.query.all()
#     return render_template('dashboard.html', users=users)

# Add this route to get user data for editing
@app.route('/get_user/<int:user_id>')
@login_required
def get_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get(user_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'username': user.username,
        'role': user.role
    })

# Update the dashboard route to include stats
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query)) | User.query.filter(User.email.contains(search_query)) if search_query else User.query.all()
    
    return render_template('dashboard.html',users=users,
        rooms_count=RoomAllocation.query.count(),
        pending_requests=Request.query.filter_by(status='pending').count(),
        feedback_count=Feedback.query.count(),
        active_tab='users',
        search_query=search_query
    )

    
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
    users = User.query.filter(User.name.contains(search_query)) | User.query.filter(User.email.contains(search_query)) if search_query else User.query.all()
    
    
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
    users = User.query.filter(User.name.contains(search_query)) | User.query.filter(User.email.contains(search_query)) if search_query else User.query.all()
    
    return render_template('dashboard.html',
                           users=users,
        rooms_count=RoomAllocation.query.count(),
        pending_requests=Request.query.filter_by(status='pending').count(),
        feedback_count=Feedback.query.count(),                   
        feedbacks=Feedback.query.order_by(Feedback.created_at.desc()).all(),
        
       
        
        active_tab='feedback'
    )

@app.route('/view_allocations')
@login_required
def view_allocations():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    search_query = request.args.get('search', '')
    users = User.query.filter(User.name.contains(search_query)) | User.query.filter(User.email.contains(search_query)) if search_query else User.query.all()
    
    
    return render_template('dashboard.html',
        users=users,
        rooms_count=RoomAllocation.query.count(),
        pending_requests=Request.query.filter_by(status='pending').count(),
        feedback_count=Feedback.query.count(),   
        allocations=RoomAllocation.query.order_by(RoomAllocation.hostel, RoomAllocation.floor).all(),
        active_tab='allocations'
    )
    
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.username = request.form['username']
        user.role = request.form['role']
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_user.html', user=user)
    


@app.route('/update_request/<int:request_id>/<status>')
@login_required
def update_request(request_id, status):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    request = Request.query.get_or_404(request_id)
    request.status = status
    db.session.commit()
    flash(f'Request marked as {status}', 'success')
    return redirect(url_for('view_requests'))

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)