from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import InternalServerError
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'my_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, name, username, email, password):
        self.name = name
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f"User  ('{self.name}', '{self.username}', '{self.email}')"

app.config['DATABASE_CREATED'] = False

@app.before_request
def create_tables():
    if not app.config['DATABASE_CREATED']:
        try:
            db.create_all()
        except Exception as e:
            raise InternalServerError("Failed to create database tables")
        app.config['DATABASE_CREATED'] = True

@app.route('/')
def home():
    return render_template('index.html')


class RoomAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(10), nullable=False)
    beds_left = db.Column(db.Integer, nullable=False, default=4)
    student_name = db.Column(db.String(50), nullable=True)

with app.app_context():
    db.create_all()


@app.route('/room_allocation', methods=['GET', 'POST'])
def room_allocation():
    if 'username' not in session:
        flash('You need to log in to access Room Allocation!', 'danger')
        return redirect(url_for('login'))    


    if request.method == 'GET':
        return render_template('room_allocation.html')

    if request.method == 'POST':
        hostel = request.form['hostel']
        floor = int(request.form['floor'])
        room_number = int(request.form['room-number'])
        room_type = request.form['room-type']
        student_name = request.form['student-name']

        room = RoomAllocation.query.filter_by(room_number=room_number).first()
        if not room:
            beds_left = 4 if room_type == "four" else (2 if room_type == "double" else 1)
            room = RoomAllocation(
                hostel=hostel, floor=floor, room_number=room_number,
                room_type=room_type, beds_left=beds_left - 1, student_name=student_name
            )
            db.session.add(room)
            db.session.commit()
            return jsonify({'message': 'Room allocated successfully!', 'success': True})
        elif room.beds_left > 0:
            room.beds_left -= 1
            room.student_name = student_name
            db.session.commit()
            return jsonify({'message': 'Room allocated successfully!', 'success': True})
        else:
            return jsonify({'message': 'Room not available!', 'success': False})



@app.route('/get_available_rooms', methods=['GET'])
def get_available_rooms():
    all_rooms = {
        "four": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "double": [201, 202, 203, 204, 205, 206, 207, 208, 209, 210],
        "single": [301, 302, 303, 304, 305, 306, 307, 308, 309, 310]
    }
    booked_rooms = [room.room_number for room in RoomAllocation.query.filter(RoomAllocation.beds_left == 0).all()]
    return jsonify({"available": all_rooms, "booked": booked_rooms})


@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


@app.route('/complaint_and_maintenance')
def complaint_and_maintenance():
    if 'username' not in session:
        flash('You need to log in to access this section', 'danger')
        return redirect(url_for('login')) 

    return render_template('complaint_and_maintenance.html')

@app.route('/feedback')
def feedback():
    if 'username' not in session:
        flash('You need to log in to access this section', 'danger')
        return redirect(url_for('login'))   


    return render_template('feedback.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')


@app.route('/hostel_details')
def hostel_details():
    return render_template('hostel_details.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

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
        else:
            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists!', 'danger')
            else:
                new_user = User(name, username, email, password)
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Signup successful!', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback()
                    flash('Failed to signup', 'danger')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return render_template('profile.html', user=user)
    else:
        flash('You need to login to access your profile', 'danger')
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)