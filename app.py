from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from camera import *
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class EmotionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()






headings = ("Name", "Album", "Artist")
df1 = music_rec()
# df1 = df1.head(15)

@app.route("/")
def index():
    return render_template("index.html", headings=headings, data=df1)

@app.route("/app")
def app_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template("app.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['username'] = user.username  # ✅ store username in session
        return jsonify({"success": True, "redirect": "/app"})
    return jsonify({"success": False, "error": "Invalid credentials"})


@app.route('/get_username')
def get_username():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'username': user.username})
    return jsonify({'username': None})


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter((User.username==username) | (User.email==email)).first():
        return jsonify({"success": False, "error": "Username or email already exists"})
    
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": True, "message": "Registration successful! You can now login."})

@app.route('/is_logged_in')
def is_logged_in():
    return jsonify({'logged_in': 'user_id' in session})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route("/get_history")
def get_history():
    if 'user_id' not in session:
        return jsonify([])

    user_id = session['user_id']
    history = EmotionHistory.query.filter_by(user_id=user_id).order_by(EmotionHistory.timestamp.desc()).all()
    return jsonify([
        {"emotion": h.emotion, "timestamp": h.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        for h in history
    ])

def gen(camera):
    while True:
        global df1
        frame, df1 = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")

@app.route("/video_feed")
def video_feed():
    return Response(gen(VideoCamera()), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/live_emotion")
def live_emotion():
    return real_time_emotion()

import random
 
@app.route("/get_recommendations")
def get_recommendations():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "User not logged in"}), 401

        is_shuffle = request.args.get("shuffle") == "1"

        if is_shuffle:
            detected_emotion = session.get('last_emotion', None)
            if not detected_emotion:
                return jsonify({"error": "No previous emotion detected for shuffle"}), 400
        else:
            session.pop('last_emotion', None)
            detected_emotion, _ = max_emotion_reccomendation()
            if not detected_emotion:
                detected_emotion = 'neutral'
            session['last_emotion'] = detected_emotion

            new_history = EmotionHistory(user_id=session['user_id'], emotion=detected_emotion)
            db.session.add(new_history)
            db.session.commit()

        # Fetch songs for detected emotion
        _, df1 = max_emotion_reccomendation(emotion=detected_emotion)

        music_data = []

        if df1 is not None and not df1.empty:
            if 'Language' not in df1.columns:
                df1['Language'] = ""
            df1.rename(columns={"Language": "language"}, inplace=True)
            df1['language'] = df1['language'].str.lower().str.strip()

            for lang in ['english', 'hindi', 'nepali']:
                lang_df = df1[df1['language'] == lang]
                sampled = lang_df.sample(n=min(10, len(lang_df)))
                music_data.extend(sampled.to_dict(orient='records'))

            # Log played songs (optional)
            

        return jsonify({
            "detected_emotion": detected_emotion,
            "music_data": music_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# from flask import request, session, jsonify

@app.route("/shuffle_recommendations")
def shuffle_recommendations():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    detected_emotion = session.get('last_emotion')
    if not detected_emotion or detected_emotion == "neutral":
        return jsonify({"detected_emotion": "neutral", "music_data": []})

    # Fetch all songs for the detected emotion
    _, df1 = max_emotion_reccomendation(emotion=detected_emotion)
    if df1 is None or df1.empty:
        return jsonify({"detected_emotion": detected_emotion, "music_data": []})

    # Normalize language column
    if 'Language' not in df1.columns:
        df1['Language'] = ""
    df1.rename(columns={"Language": "language"}, inplace=True)
    df1['language'] = df1['language'].str.lower().str.strip()

    # Fetch previously shown song URLs for each language
    shown_urls = session.get('shown_urls_by_language', {
        "english": [],
        "hindi": [],
        "nepali": []
    })

    final_songs = []

    for lang in ['english', 'hindi', 'nepali']:
        lang_df = df1[df1['language'] == lang]

        # Filter out already shown songs for this language
        unseen = lang_df[~lang_df['SpotifyURL'].isin(shown_urls.get(lang, []))]

        # If not enough unseen, reset the list for this language
        if len(unseen) < 10:
            unseen = lang_df
            shown_urls[lang] = []

        # Sample 10 songs
        sampled = unseen.sample(n=min(10, len(unseen)))
        final_songs.extend(sampled.to_dict(orient='records'))

        # Update shown URLs for this language
        new_urls = sampled['SpotifyURL'].tolist()
        shown_urls[lang].extend(new_urls)

    # Save updated shown songs to session
    session['shown_urls_by_language'] = shown_urls

    return jsonify({
        "detected_emotion": detected_emotion,
        "music_data": final_songs
    })





# from flask import render_template, session

# @app.route('/dashboard')
# def dashboard():
#     username = session.get('username')  # Assuming username is stored in session
#     return render_template('dashboard.html', username=username)

# from flask import session, render_template

# @app.route('/dashboard')
# def dashboard():
#     username = session.get('username')  # make sure this is set during login
#     return render_template('dashboard.html', username=username)

@app.route('/image', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        image = Image.open(file.stream)
        image_array = np.array(image)
        [picture, detected_emotion] = emotion_rec(image_array)

        if 'user_id' in session:
            new_history = EmotionHistory(user_id=session['user_id'], emotion=detected_emotion)
            db.session.add(new_history)
            db.session.commit()

        return jsonify({"emotion": detected_emotion})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == "__main__":
    app.debug = True
    app.run(port=6969)
