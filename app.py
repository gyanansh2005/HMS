from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import InternalServerError
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config['SECRET_KEY'] = 'my_secret_key'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Corrected typo
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()


class RoomAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(10), nullable=False)
    beds_left = db.Column(db.Integer, nullable=False, default=4)
    student_name = db.Column(db.String(50), nullable=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/room_allocation', methods=['GET', 'POST'])
@login_required
def room_allocation():
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
    return render_template('room_allocation.html')

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
@login_required
def complaint_and_maintenance():
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
    if 'username' not in session:
        flash('You need to log in to access this section', 'danger')
        return redirect(url_for('login'))  
    return render_template('hostel_details.html')


@app.route('/about')
def about():
    return render_template('about.html')


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
            session['username'] = user.username  # Store username in session
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

@app.route('/signup' , methods=['GET', 'POST'])
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

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)
