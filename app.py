from flask import Flask, render_template, request, redirect, url_for, flash, session
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

@app.route('/room_allocation')
def room_allocation():
    return render_template('room_allocation.html')

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/Feedback')
def Feedback():
    return render_template('Feedback.html')

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