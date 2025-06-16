from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from twilio.rest import Client
import os
import random
import sendgrid
from sendgrid.helpers.mail import Mail
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

# MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client['canteen']
users = db['users']
email_otp_db = db['email_otp']
phone_otp_db = db['phone_otp']

# Twilio (Mobile OTP)
twilio_client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
twilio_phone = os.getenv("TWILIO_PHONE")

# SendGrid (Email OTP)
sendgrid_client = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
from_email = os.getenv("FROM_EMAIL") 
# -------------------- Routes --------------------

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        email = request.form.get('email')
        phone = request.form.get('phone_number')

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        if users.find_one({'username': username}):
            flash("Username already exists", "danger")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        user_data = {
            'username': username,
            'password': hashed_pw,
            'email': email,
            'phone': phone
        }
        users.insert_one(user_data)
        flash("Registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash("Login successful!", "success")
            return redirect(url_for('menu'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"Welcome to the menu, {session['user']}!"


# ------------------ OTP Routes ------------------
@app.route('/send_email_otp', methods=['POST'])
def send_email_otp():
    email = request.form.get('email')
    otp = str(random.randint(100000, 999999))
    email_otp_db.update_one({'email': email}, {'$set': {'otp': otp}}, upsert=True)

    message = Mail(
        from_email=from_email,
        to_emails=email,
        subject='Your Email OTP Verification Code',
        plain_text_content=f'Your OTP is {otp}. Use this to verify your email.'
    )

    try:
        sendgrid_client.send(message)
        return jsonify({'message': 'OTP sent to your email.'})
    except Exception as e:
        return jsonify({'error': 'Failed to send email OTP.'}), 500


@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.form.get('phone')
    otp = str(random.randint(100000, 999999))
    phone_otp_db.update_one({'phone': phone}, {'$set': {'otp': otp}}, upsert=True)

    try:
        twilio_client.messages.create(
            body=f"Your Canteen OTP is: {otp}",
            from_=twilio_phone,
            to=phone
        )
        return jsonify({'message': 'OTP sent to your phone.'})
    except Exception as e:
        return jsonify({'error': 'Failed to send SMS OTP.'}), 500


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    phone = request.form.get('phone')
    otp = request.form.get('otp')
    record = phone_otp_db.find_one({'phone': phone})
    if record and record['otp'] == otp:
        return jsonify({'message': 'Phone verified successfully!'})
    else:
        return jsonify({'error': 'Invalid OTP'}), 400


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))


# -------------------- Run --------------------
if __name__ == '__main__':
    app.run(debug=True)
