from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random, smtplib, ssl
from datetime import datetime
import pandas as pd

# ===============================================================
# SWASTHSATHI - STABLE DEPLOYMENT VERSION (Q&A LOGIC)
# ===============================================================
print("--- SWASTHSATHI (STABLE Q&A VERSION) IS RUNNING ---")
# ===============================================================

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- Database Setup ----------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///symptom_checker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Load Dataset for Q&A Logic ----------
try:
    df = pd.read_csv('Disease_symptom_and_patient_profile_dataset.csv')
    symptom_columns = ['Fever', 'Cough', 'Fatigue', 'Difficulty Breathing']
    SYMPTOM_MAP = {symptom.lower(): symptom for symptom in symptom_columns}
except FileNotFoundError:
    print("FATAL ERROR: Disease_symptom_and_patient_profile_dataset.csv not found.")
    df = pd.DataFrame()

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
SENDER_PASSWORD = "tqzcxjencxroglgh" # In production, use os.getenv("SENDER_PASSWORD")
otp_store = {}

# ---------- Helper Function ----------
def get_next_symptom(possible_diseases, asked_symptoms):
    if not possible_diseases:
        return None
    relevant_df = df[df['Disease'].isin(possible_diseases)]
    for symptom in symptom_columns:
        if symptom not in asked_symptoms:
            if len(relevant_df[symptom].unique()) > 1:
                return symptom
    return None

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
    email = session.get('email')
    session.clear()
    session['logged_in'] = True
    session['email'] = email
    session['user_symptoms'] = {}
    session['asked_symptoms'] = []
    session['possible_diseases'] = df['Disease'].unique().tolist()
    symptoms_input = request.form.get('symptoms', '').lower().split(',')
    for user_symptom in symptoms_input:
        symptom_clean = user_symptom.strip()
        if symptom_clean in SYMPTOM_MAP:
            column_name = SYMPTOM_MAP[symptom_clean]
            session['user_symptoms'][column_name] = 'Yes'
            if column_name not in session['asked_symptoms']:
                session['asked_symptoms'].append(column_name)
    return redirect(url_for('ask_question'))

@app.route('/question', methods=['GET', 'POST'])
def ask_question():
    if not session.get('logged_in'): return redirect(url_for('login'))
    session.setdefault('user_symptoms', {})
    session.setdefault('asked_symptoms', [])
    session.setdefault('possible_diseases', df['Disease'].unique().tolist())
    if request.method == 'POST':
        symptom = request.form['symptom']
        answer = 'Yes' if request.form['answer'] == 'yes' else 'No'
        session['user_symptoms'][symptom] = answer
        if symptom not in session['asked_symptoms']:
            session['asked_symptoms'].append(symptom)
    
    possible_diseases = session.get('possible_diseases', [])
    current_symptoms = session.get('user_symptoms', {})
    
    if possible_diseases:
        diseases_to_remove = set()
        for disease in possible_diseases:
            disease_profile = df[df['Disease'] == disease].iloc[0]
            for sym, value in current_symptoms.items():
                if sym in disease_profile.index and disease_profile[sym] != value:
                    diseases_to_remove.add(disease)
                    break
        session['possible_diseases'] = [d for d in possible_diseases if d not in diseases_to_remove]
    
    current_possibilities = session.get('possible_diseases', [])
    next_symptom = get_next_symptom(current_possibilities, session.get('asked_symptoms', []))
    
    if not next_symptom or not current_possibilities or len(current_possibilities) == 1:
        if current_possibilities:
            final_disease = current_possibilities[0]
        else:
            final_disease = "Could not determine a match based on symptoms."
        
        symptoms_str = ", ".join([s for s, v in current_symptoms.items() if v == 'Yes'])
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = History(email=session.get('email'), symptoms=symptoms_str, disease=final_disease, timestamp=timestamp_str)
        db.session.add(record)
        db.session.commit()
        return render_template('result.html', diseases=final_disease, tips="Consult a doctor for an accurate diagnosis.", doctors="A General Physician is recommended.")
    else:
        session.modified = True
        return render_template('question.html', symptom=next_symptom)

@app.route('/history')
def history():
    if not session.get('logged_in'): return redirect(url_for('login'))
    records = History.query.filter_by(email=session['email']).order_by(History.timestamp.desc()).all()
    return render_template('history.html', records=records)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)