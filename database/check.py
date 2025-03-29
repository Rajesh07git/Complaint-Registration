import sqlite3

# Connect to the database
conn = sqlite3.connect('complaints.db')
c = conn.cursor()

# Fetch all complaints
c.execute("SELECT * FROM complaints")
complaints = c.fetchall()

for complaint in complaints:
    print(complaint)  # This will print each complaint entry in the database
