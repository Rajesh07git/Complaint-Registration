import sqlite3
import pickle
import re
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Load the trained ML model, label encoder, and vectorizer
with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

with open("model/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

with open("model/tfidf_vectorizer.pkl", "rb") as f:
    tfidf_vectorizer = pickle.load(f)

# Initialize database
conn = sqlite3.connect("database/complaints.db", timeout=10, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    mess TEXT,
    date TEXT,
    complaint_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'Pending'
)""")
conn.commit()

# Create users table (for student login)
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
""")
conn.commit()

app = Flask(__name__, template_folder='client')


def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', str(text), re.I)  # Remove special characters
    return text.lower().strip()

@app.route('/')
def index():
    return render_template('student_login.html')  # Default to student login

@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/complaint')
def complaint():
    return render_template('complaint.html')

@app.route('/logout')
def logout():
    return render_template('student_login.html')

@app.route('/view_complaints')
def view_complaints():
    return render_template('view_complaints.html')

@app.route('/submit', methods=['POST'])
def submit_complaint():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        mess = data.get('mess')
        date = data.get('date')
        description = data.get('description')

        if not all([name, email, mess, date, description]):
            return jsonify({"error": "All fields are required."}), 400

        # Predict category using ML model
        cleaned_desc = preprocess_text(description)
        complaint_vectorized = tfidf_vectorizer.transform([cleaned_desc])
        predicted_category = label_encoder.inverse_transform(model.predict(complaint_vectorized))[0]
        predicted_category = predicted_category.replace('/', '_')

        # Insert into database
        c.execute("INSERT INTO complaints (name, email, mess, date, complaint_type, description) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, email, mess, date, predicted_category, description))
        conn.commit()

        complaint_id = c.lastrowid  # Get the complaint ID

        return jsonify({
            "message": "Complaint Registered Successfully",
            "category": predicted_category,
            "complaint_id": complaint_id
        }), 201
    except Exception as e:
        print(f"Error in /submit: {str(e)}")
        return jsonify({"error": f"Failed to submit complaint: {str(e)}"}), 500

@app.route('/status/<int:complaint_id>', methods=['GET'])
def check_status(complaint_id):
    try:
        c.execute("SELECT status FROM complaints WHERE id=?", (complaint_id,))
        result = c.fetchone()
        if result:
            return jsonify({"status": result[0]})
        return jsonify({"error": "Complaint not found"}), 404
    except Exception as e:
        print(f"Error in /status/{complaint_id}: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/complaints/<category>', methods=['GET'])
def get_complaints_by_category(category):
    try:
        category = category.replace('/', '_').strip()  # Ensure no extra spaces
        print(f"Fetching complaints for category: {category}")
        c.execute("SELECT * FROM complaints WHERE complaint_type=?", (category,))

        complaints = c.fetchall()

        if complaints:
            return jsonify({"complaints": complaints})
        return jsonify({"message": "No complaints found in this category."}), 404
    except Exception as e:
        print(f"Error in /complaints/{category}: {str(e)}")
        return jsonify({"error": f"Failed to retrieve complaints: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
