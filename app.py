from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import cohere
import os
from werkzeug.utils import secure_filename
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

app = Flask('interview')
app.config['1c7d6f9e0a5b3c7d8e2f1a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f'] = os.getenv('1c7d6f9e0a5b3c7d8e2f1a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt', 'doc', 'docx'}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
co = cohere.Client(os.getenv('hAdn1u4a6CPMbQwChFEdsk4ukeB0IVlsqldSMOtp'))

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    resumes = db.relationship('Resume', backref='user', lazy=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password)  # In production, hash passwords!
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In production, use password hashing!
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    if 'resume_file' not in request.files:
        flash('No file selected')
        return redirect(url_for('dashboard'))
    
    file = request.files['resume_file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('dashboard'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file content
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Enhance resume with Cohere
        enhanced_resume = co.generate(
            model='command',
            prompt=f"Enhance this resume for better formatting and professionalism:\n\n{content}",
            max_tokens=1000
        ).generations[0].text
        
        # Save to database
        new_resume = Resume(filename=filename, content=enhanced_resume, user_id=current_user.id)
        db.session.add(new_resume)
        db.session.commit()
        
        return render_template('dashboard.html', resume=enhanced_resume)
    
    flash('Invalid file type')
    return redirect(url_for('dashboard'))

@app.route('/interview', methods=['POST'])
@login_required
def interview():
    job_role = request.form['job_role']
    resume = request.form['resume']
    
    # Generate interview questions with Cohere
    questions = co.generate(
        model='command',
        prompt=f"Generate 5 technical interview questions for a {job_role} position based on this resume:\n\n{resume}",
        max_tokens=500
    ).generations[0].text.split('\n')
    
    # Generate TTS audio for questions
    tts_files = []
    for i, question in enumerate(questions):
        if question.strip():
            tts_filename = f"static/tts/question_{i}.mp3"
            tts = gTTS(text=question, lang='en')
            tts.save(tts_filename)
            tts_files.append(tts_filename)
    
    return render_template('interview.html', questions=questions, tts_files=tts_files)

@app.route('/feedback', methods=['POST'])
@login_required
def feedback():
    responses = request.form.getlist('responses')
    
    # Evaluate responses with Cohere
    feedback = co.generate(
        model='command',
        prompt=f"Evaluate these interview responses and provide constructive feedback:\n\n{responses}",
        max_tokens=500
    ).generations[0].text
    
    return jsonify({'feedback': feedback})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)