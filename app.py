import sqlite3
from datetime import datetime

# Define your tariff structure here (Cost per unit)
UNIT_RATE = 15.00  # Adjust this to match your local energy tier rate

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect("electricity_data.db")
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
    """Retrieves the most recent meter reading from the database."""
    conn = sqlite3.connect("electricity_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT meter_reading FROM daily_usage ORDER BY reading_date DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def add_reading(date_str, current_reading):
    """Calculates units consumed and costs, then saves the entry to the database."""
    last_reading = get_last_reading()
    
    # Calculate daily consumption
    if last_reading > 0:
        units_consumed = current_reading - last_reading
        if units_consumed < 0:
            print("❌ Warning: Current reading is lower than the last reading. Resetting consumption to 0.")
            units_consumed = 0
    else:
        units_consumed = 0.0  # Initial benchmark entry

    # Calculate cost
    calculated_cost = units_consumed * UNIT_RATE

    try:
        conn = sqlite3.connect("electricity_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (reading_date, meter_reading, units_consumed, calculated_cost)
            VALUES (?, ?, ?, ?)
        """, (date_str, current_reading, units_consumed, calculated_cost))
        conn.commit()
        conn.close()
        print(f"✅ Data saved! Date: {date_str} | Units Used: {units_consumed} | Est. Cost: ${calculated_cost:.2f}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: A reading already exists for {date_str}.")

def view_history():
    """Displays all records saved in the database."""
    conn = sqlite3.connect("electricity_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT reading_date, meter_reading, units_consumed, calculated_cost FROM daily_usage ORDER BY reading_date ASC")
    rows = cursor.fetchall()
    conn.close()
    
    print("\n--- Saved Electricity Logs ---")
    print(f"{'Date':<12} | {'Meter Reading':<15} | {'Units Used':<12} | {'Est. Cost':<10}")
    print("-" * 58)
    for row in rows:
        print(f"{row[0]:<12} | {row[1]:<15} | {row[2]:<12} | ${row[3]:<10.2f}")
    print("\n")

def main():
    init_db()
    while True:
        print("💡 Electricity Tracker Menu 💡")
        print("1. Log Daily Meter Reading")
        print("2. View History & Total Bill")
        print("3. Exit")
        choice = input("Select an option (1-3): ")

        if choice == '1':
            # Allows updating past dates if you miss a day
            date_input = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
            if not date_input:
                date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                try:
                    # Validate date formatting
                    datetime.strptime(date_input, "%Y-%m-%d")
                    date_str = date_input
                except ValueError:
                    print("❌ Invalid date format. Please use YYYY-MM-DD.")
                    continue
            
            try:
                reading = float(input("Enter current meter reading (kWh): "))
                add_reading(date_str, reading)
            except ValueError:
                print("❌ Invalid input. Please enter a numerical value for the meter.")
                
        elif choice == '2':
            view_history()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("❌ Invalid selection. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    main()
