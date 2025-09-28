from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random, smtplib, ssl
from datetime import datetime
import pandas as pd
import joblib
import numpy as np

# ===============================================================
# SWASTHSATHI - FINAL ML MODEL VERSION
# ===============================================================
print("--- SWASTHSATHI (ML MODEL VERSION) IS RUNNING ---")
# ===============================================================

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- Database Setup ----------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///symptom_checker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Load the Trained Model and Columns ----------
try:
    model = joblib.load('disease_model.pkl')
    model_columns = joblib.load('model_columns.pkl')
    print("Model and columns loaded successfully.")
except FileNotFoundError:
    print("FATAL ERROR: Model files not found. Please run train_model.py first.")
    model = None
    model_columns = []

# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    symptoms = db.Column(db.String(500))
    disease = db.Column(db.String(200))
    timestamp = db.Column(db.String(100))

# ---------- Email Config ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "swasthsathi@gmail.com"
SENDER_PASSWORD = "segwwdcqgydwsnaw"
otp_store = {}

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        otp = str(random.randint(100000, 999999))
        otp_store[email] = otp
        session['email'] = email
        user = User.query.filter_by(email=email).first()
        if not user:
            new_user = User(email=email)
            db.session.add(new_user)
            db.session.commit()
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                message = f"Subject: SwasthSathi OTP\n\nYour OTP is: {otp}"
                server.sendmail(SENDER_EMAIL, email, message)
            return redirect(url_for('verify_otp'))
        except Exception as e:
            return f"<h1>Error sending OTP: {e}</h1>"
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('email')
    if not email: return redirect(url_for('login'))
    if request.method == 'POST':
        if otp_store.get(email) == request.form['otp']:
            otp_store.pop(email, None)
            session['logged_in'] = True
            return redirect(url_for('symptom_checker'))
        else:
            return render_template('verify.html', error="Invalid OTP, try again.")
    return render_template('verify.html')

@app.route('/symptom')
def symptom_checker():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if model is None or not model_columns.any():
        return "Model not loaded. Please train the model first by running train_model.py"

    # Get the list of symptoms from the user input
    symptoms_input = request.form.get('symptoms', '').lower()
    user_symptoms = [s.strip().replace(' ', '_') for s in symptoms_input.split(',')]

    # Create an input vector for the model (an array of zeros)
    input_vector = pd.DataFrame(columns=model_columns)
    input_vector.loc[0] = 0

    # Set the user's symptoms to 1 in the input vector
    for symptom in user_symptoms:
        if symptom in model_columns:
            input_vector.loc[0, symptom] = 1
            
    # Make the prediction
    prediction = model.predict(input_vector)[0]
    
    # Save to history
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = History(email=session.get('email'), symptoms=symptoms_input, disease=prediction, timestamp=timestamp_str)
    db.session.add(record)
    db.session.commit()
    
    return render_template('result.html', diseases=prediction, tips="Consult a doctor for an accurate diagnosis.", doctors="A General Physician is recommended.")


@app.route('/history')
def history():
    if not session.get('logged_in'): return redirect(url_for('login'))
    records = History.query.filter_by(email=session['email']).order_by(History.timestamp.desc()).all()
    return render_template('history.html', records=records)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/get_symptoms')
def get_symptoms():
    if not model_columns.any():
        return "Model columns not loaded."
    
    # Convert symptom names to a more user-friendly format (e.g., 'skin_rash' -> 'skin rash')
    symptom_list = [col.replace('_', ' ') for col in model_columns]
    return symptom_list

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)