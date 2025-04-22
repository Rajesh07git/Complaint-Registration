import sqlite3
import pickle
import re
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

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

# Create complaints table
c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    mess TEXT,
    date TEXT,
    complaint_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'Pending',
    submission_date TEXT,
    roll_number TEXT
)""")

# Create admin table
c.execute("""
CREATE TABLE IF NOT EXISTS admins (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    category TEXT
)""")

# Insert default admin if not exists
c.execute("SELECT * FROM admins WHERE email=?", ("admin@nitk.edu.in",))
if not c.fetchone():
    c.execute("INSERT INTO admins (email, password, category) VALUES (?, ?, ?)", 
              ("admin@nitk.edu.in", generate_password_hash("admin@1234"), "All"))
    conn.commit()

app = Flask(__name__, template_folder='client', static_folder='static')
app.secret_key = 'nitk_mess_complaint_system'

def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', str(text), re.I)  # Remove special characters
    return text.lower().strip()

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/complaint')
def complaint():
    return render_template('complaint.html')

@app.route('/complaint_status')
def complaint_status():
    return render_template('complaint_status.html')

@app.route('/my_complaints')
def my_complaints():
    return render_template('my_complaints.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/view_complaints')
def view_complaints():
    category = request.args.get('category', 'Food Hygiene')
    return render_template('view_complaints.html', selected_category=category)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/submit', methods=['POST'])
def submit_complaint():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        roll_number = data.get('rollNumber')
        mess = data.get('mess')
        date = data.get('date')
        description = data.get('description')

        if not all([name, email, mess, date, description, roll_number]):
            return jsonify({"error": "All fields are required."}), 400

        # Predict category using ML model
        cleaned_desc = preprocess_text(description)
        complaint_vectorized = tfidf_vectorizer.transform([cleaned_desc])
        predicted_category = label_encoder.inverse_transform(model.predict(complaint_vectorized))[0]
        predicted_category = predicted_category.replace('/', '_')

        # Insert into database with current date
        submission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO complaints (name, email, mess, date, complaint_type, description, status, submission_date, roll_number) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, mess, date, predicted_category, description, "Pending", submission_date, roll_number))
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
        if category == "All":
            c.execute("SELECT * FROM complaints ORDER BY submission_date DESC")
        else:
            category = category.replace('/', '_').strip()  # Ensure no extra spaces
            c.execute("SELECT * FROM complaints WHERE complaint_type=? ORDER BY submission_date DESC", (category,))

        complaints = c.fetchall()

        if complaints:
            return jsonify({"complaints": complaints})
        return jsonify({"message": "No complaints found in this category."}), 404
    except Exception as e:
        print(f"Error in /complaints/{category}: {str(e)}")
        return jsonify({"error": f"Failed to retrieve complaints: {str(e)}"}), 500
    
@app.route('/update_status/<int:complaint_id>', methods=['POST'])
def update_status(complaint_id):
    try:
        status = request.json.get('status', 'Completed')
        # Update the status of the complaint
        c.execute("UPDATE complaints SET status = ? WHERE id = ?", (status, complaint_id))
        conn.commit()
        
        # Fetch updated complaint details
        c.execute("SELECT id, name, mess, date, status FROM complaints WHERE id = ?", (complaint_id,))
        complaint = c.fetchone()
        
        # Prepare the updated status message
        updated_text = f"ID: {complaint[0]}, Name: {complaint[1]}, Mess: {complaint[2]}, Date: {complaint[3]}, Status: {complaint[4]}"
        
        return jsonify({"success": True, "updatedText": updated_text})
    except Exception as e:
        print(f"Error updating status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/complaint_stats', methods=['GET'])
def get_complaint_stats():
    try:
        # Get count of complaints by status
        c.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
        results = c.fetchall()
        
        stats = {}
        for status, count in results:
            status_key = status.lower().replace(' ', '_')
            # Map "completed" to "resolved" for the frontend
            if status_key == "completed":
                stats["resolved"] = count
            else:
                stats[status_key] = count
            
        # Ensure all statuses have a value
        for status in ['pending', 'in_progress', 'resolved']:
            if status not in stats:
                stats[status] = 0
                
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting complaint stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/student_complaints', methods=['GET'])
def get_student_complaints():
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({"error": "Email is required"}), 400
            
        c.execute("""
        SELECT id, name, roll_number, mess, date, complaint_type, description, status 
        FROM complaints 
        WHERE email = ? 
        ORDER BY submission_date DESC
        """, (email,))
        
        complaints = c.fetchall()
        result = []
        
        for complaint in complaints:
            result.append({
                "id": complaint[0],
                "name": complaint[1],
                "roll_number": complaint[2],
                "mess": complaint[3],
                "date": complaint[4],
                "category": complaint[5],
                "description": complaint[6],
                "status": complaint[7]
            })
            
        return jsonify({"complaints": result})
    except Exception as e:
        print(f"Error getting student complaints: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/category_distribution', methods=['GET'])
def get_category_distribution():
    try:
        c.execute("SELECT complaint_type, COUNT(*) FROM complaints GROUP BY complaint_type")
        results = c.fetchall()
        
        categories = {}
        for category, count in results:
            categories[category] = count
            
        return jsonify(categories)
    except Exception as e:
        print(f"Error getting category distribution: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add these imports to the top of your file with the other imports
from datetime import datetime, timedelta
import calendar

# Add this new endpoint after your other API endpoints
@app.route('/api/complaints_timeline', methods=['GET'])
def complaints_timeline():
    try:
        # Define the time period - last 6 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # Approximately 6 months
        
        # Format dates to match your database format
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # Initialize lists to store our results
        months = []
        new_complaints = []
        resolved_complaints = []
        
        # Get month names for the last 6 months
        current_date = start_date
        while current_date <= end_date:
            month_name = current_date.strftime("%B")  # Month name (e.g., "January")
            months.append(month_name)
            
            # Format month boundaries for SQL queries
            month_start = f"{current_date.year}-{current_date.month:02d}-01"
            
            # Get last day of current month
            _, last_day = calendar.monthrange(current_date.year, current_date.month)
            month_end = f"{current_date.year}-{current_date.month:02d}-{last_day}"
            
            # Count new complaints submitted in this month
            c.execute("""
                SELECT COUNT(*) FROM complaints 
                WHERE submission_date BETWEEN ? AND ?
            """, (month_start, month_end + " 23:59:59"))
            new_count = c.fetchone()[0]
            new_complaints.append(new_count)
            
            # Count complaints resolved in this month
            c.execute("""
                SELECT COUNT(*) FROM complaints 
                WHERE status = 'Completed' 
                AND submission_date BETWEEN ? AND ?
            """, (month_start, month_end + " 23:59:59"))
            resolved_count = c.fetchone()[0]
            resolved_complaints.append(resolved_count)
            
            # Move to next month
            if current_date.month == 12:
                current_date = datetime(current_date.year + 1, 1, 1)
            else:
                current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        # Return the results as JSON
        return jsonify({
            'labels': months,
            'new_complaints': new_complaints,
            'resolved_complaints': resolved_complaints
        })
        
    except Exception as e:
        print(f"Error getting complaints timeline: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)