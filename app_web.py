from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "electricity_data.db"
UNIT_RATE = 15.00  # Adjust this to match your local rate per unit

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_date TEXT UNIQUE,
            meter_reading REAL,
            units_consumed REAL,
            calculated_cost REAL
        )
    """)
    conn.commit()
    conn.close()

def get_last_reading():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT meter_reading FROM daily_usage ORDER BY reading_date DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

# HTML Template with an embedded clean modern CSS style
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Electricity Bill Tracker</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 40px; color: #333; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h1, h2 { color: #2c3e50; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="date"], input[type="number"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-radius; font-size: 16px; }
        button { background: #2ecc71; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; }
        button:hover { background: #27ae60; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #34495e; color: white; }
        tr:hover { background-color: #f9f9f9; }
        .alert { padding: 12px; background-color: #e74c3c; color: white; border-radius: 6px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💡 Electricity Bill Tracker</h1>
        
        {% if error %}
            <div class="alert">{{ error }}</div>
        {% endif %}

        <h2>Log New Meter Reading</h2>
        <form action="/add" method="POST">
            <div class="form-group">
                <label>Date (Leave blank for today):</label>
                <input type="date" name="reading_date">
            </div>
            <div class="form-group">
                <label>Current Meter Reading (kWh):</label>
                <input type="number" step="0.01" name="meter_reading" required placeholder="e.g. 1245.3">
            </div>
            <button type="submit">Save Entry to Database</button>
        </form>

        <h2>📊 Saved Usage Logs</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Meter Reading (kWh)</th>
                <th>Units Used (Daily)</th>
                <th>Estimated Cost</th>
            </tr>
            {% for row in history %}
            <tr>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }} kWh</td>
                <td>{{ row[3] }} kWh</td>
                <td>${{ "%.2f"|format(row[4]) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    error = request.args.get('error')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_usage ORDER BY reading_date DESC")
    history = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, history=history, error=error)

@app.route('/add', methods=['POST'])
def add_entry():
    date_str = request.form.get('reading_date')
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    try:
        current_reading = float(request.form.get('meter_reading'))
    except ValueError:
        return redirect(url_for('index', error="Invalid numerical input for meter reading."))

    last_reading = get_last_reading()
    
    if last_reading > 0:
        units_consumed = current_reading - last_reading
        if units_consumed < 0:
            units_consumed = 0.0
    else:
        units_consumed = 0.0

    calculated_cost = units_consumed * UNIT_RATE

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (reading_date, meter_reading, units_consumed, calculated_cost)
            VALUES (?, ?, ?, ?)
        """, (date_str, current_reading, units_consumed, calculated_cost))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        return redirect(url_for('index', error=f"An entry already exists for the date {date_str}."))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
