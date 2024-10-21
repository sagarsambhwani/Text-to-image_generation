from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash # type: ignore
import mysql.connector # type: ignore
from passlib.hash import sha256_crypt # type: ignore
from io import BytesIO
import requests # type: ignore
import os
import re

app = Flask(__name__)

app.secret_key = os.urandom(24) 

print("Starting the Flask application...")  # Add this at the top of the file

# # Set secret key for session
# app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

HUGGINGFACE_API_KEY = "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"

# Verify the Hugging Face API key exists
if not HUGGINGFACE_API_KEY:
    raise ValueError("Hugging Face API key not found in environment variables.")

# Hugging Face API settings
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}


# Set database credentials (environment variables or hardcoded for testing)
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "Centralperk2=")

try:
    # Connect to the MySQL database
    db = mysql.connector.connect(
        host="localhost",
        user=DB_USER,
        password=DB_PASS,
        database="image_gen_app"
    )
    cursor = db.cursor()
    print("Connected to MySQL successfully.")

except mysql.connector.Error as err:
    # Error handling
    print(f"Error connecting to MySQL: {err}")
    exit(1)


# Route: Login Page
@app.route('/')
def login():
    return render_template('login.html')

# Route: Authenticate User
@app.route('/login', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']

    try:
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and sha256_crypt.verify(password, user[1]):
            session['user_id'] = user[0]
            return redirect(url_for('prompt'))  # Update 'prompt' to the correct route
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# Route: Register User
@app.route('/register', methods=['GET', 'POST'])  # Allow both GET and POST methods
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = sha256_crypt.hash(request.form['password'])

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            return redirect(url_for('register'))  # Redirect back to register on error
    return render_template('register.html')  # Render register.html for GET requests


# Route: Prompt Page
@app.route('/prompt')
def prompt():
    if 'user_id' in session:
        return render_template('prompt.html')
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

# Route: Generate Image
@app.route('/generate_image', methods=['POST'])
def generate_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    text_prompt = request.form['text_prompt']
    sanitized_prompt = re.sub(r'[^a-zA-Z0-9]', '_', text_prompt)

    # API request to Hugging Face
    api_payload = {"inputs": text_prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=api_payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}", 500
    except requests.exceptions.RequestException as e:
        return f"Error generating image: {e}", 500

    # Check if the response is an image
    if response.headers['Content-Type'] != 'image/jpeg':
        return f"Error: Expected an image but got {response.headers['Content-Type']}", 500

    # Load the image from the API response
    image_data = response.content
    img_io = BytesIO(image_data)
    img_io.seek(0)

    # Save the image to disk
    img_path = f'static/images/{session["user_id"]}_{sanitized_prompt}.jpg'
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    with open(img_path, 'wb') as f:
        f.write(image_data)

    # Save the prompt and image path in the database
    try:
        cursor.execute(
            "INSERT INTO prompts (user_id, prompt_text, image_path) VALUES (%s, %s, %s)",
            (session['user_id'], text_prompt, img_path)
        )
        db.commit()
    except mysql.connector.Error as err:
        db.rollback()  # Rollback in case of error
        return f"Error: {err}", 500

    # Serve the generated image
    return send_file(img_io, mimetype='image/jpeg')

# Main entry point
if __name__ == '__main__':
    print("Running Flask app...")  # Add this before app.run()
    app.run(debug=True)
