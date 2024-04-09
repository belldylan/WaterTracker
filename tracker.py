from datetime import date, timedelta, datetime
import sqlite3
import csv


class WaterTracker:
  daily_goal = 64 
  
  # Creates/Opens database file
  def __init__(self, db_file='db.sqlite'):
    self.conn = sqlite3.connect(db_file)
    self.cursor = self.conn.cursor()
    self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS drinks (
          id INTEGER PRIMARY KEY,
          date TEXT,
          type TEXT,
          ounces REAL
        );
    """)
    self.conn.commit()
    

  # Creates a backup by copying the current database file
  def backup_database(self, db_file = 'db.sqlite', backup_file='backup.csv'):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Fetch all records from the drinks table
        cursor.execute("SELECT * FROM drinks;")
        rows = cursor.fetchall()

        # Write records to a CSV file
        with open(f"{backup_file}", "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            # Write the header row with column names
            csv_writer.writerow([description[0] for description in cursor.description])
            # Write the data rows
            csv_writer.writerows(rows)

        print("Backup completed successfully!")

    except sqlite3.Error as e:
        print(f"Error during backup: {e}")

    finally:
        if conn:
            conn.close()
      
  # Adds drink entry to current date
  def add_current_entry(self):
    target_date = str(date.today())
    drink_type = input("Enter the type of drink (or leave empty to cancel): ")
    
    if drink_type == "":
        print("Operation canceled.")
        return

    ounces_consumed = input(f"Enter the ounces of {drink_type} consumed on {target_date}: ")

    if not ounces_consumed:
        print("Operation canceled.")
        return
    
    ounces_consumed = float(ounces_consumed)
    
    # Assuming self.db is your SQLite database connection
    cursor = self.conn.cursor()
    
    # Inserting data into the SQLite table
    cursor.execute("INSERT INTO drinks (date, type, ounces) VALUES (?, ?, ?)",
                  (target_date, drink_type, ounces_consumed))
    
    # Committing the transaction
    self.conn.commit()
    
    print(f"Entry added for {target_date}: {ounces_consumed} ounces of {drink_type}.")
    
  # Adds drink entry to previous date  
  def add_previous_entry(self):
    target_date = input("Enter the date (YYYY-MM-DD) to add the entry to (or leave empty to cancel): ")

    if not target_date:
      print("Operation canceled.")
      return

    try:
      target_date = datetime.strptime(target_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
      print("Invalid date format. Operation canceled.")
      return
      
    drink_type = input("Enter the type of drink (or leave empty to cancel): ")

    if not drink_type:
      print("Operation canceled.")
      return

    ounces_consumed = input(f"Enter the ounces of {drink_type} consumed on {target_date}: ")
    
    if not ounces_consumed:
      print("Operation canceled.")
      return
    
    ounces_consumed = float(ounces_consumed)
    
    cursor = self.conn.cursor()
    
    cursor.execute("INSERT INTO drinks (date, type, ounces) VALUES (?, ?, ?)",
                  (target_date, drink_type, ounces_consumed))
    
    self.conn.commit()
    
    print(f"Entry added for {target_date}: {ounces_consumed} ounces of {drink_type}.")
    
  # Removes entry by id  
  def remove_entry_id(self):
    entry_id = input(f"\nEnter the ID of the entry to remove (or leave empty to cancel): ")
    try:
      entry_id = int(entry_id)
    except ValueError:
      print("Invalid entry ID. Operation canceled.")
      return
    
    self.cursor.execute("SELECT id FROM drinks WHERE id=?", (entry_id,))
    result = self.cursor.fetchone()

    if result:
      self.cursor.execute("DELETE FROM drinks WHERE id=?", (entry_id,))
      self.conn.commit()
      print(f"Drink with id {entry_id} has been removed.")
    else:
      print(f"Record with id {entry_id} does not exist.")
    
  # Removes group of entries by Day/Week/All      
  def remove_group_entry(self):
    print("Select the scope to clear entries:")
    print("1. Day")
    print("2. Week")
    print("3. All")

    choice = input("Enter your choice (1-3) or leave empty to cancel: ")
    
    if not choice:
      print("Operation canceled.")
      return

    if choice == '1': # Day
      target_date = input("Enter the date (YYYY-MM-DD) to clear entries for or leave empty to cancel: ")
      if not target_date:
        print("Operation canceled.")
        return
      else:
        self.cursor.execute("SELECT date FROM drinks WHERE date=?", (target_date,))
        result = self.cursor.fetchone()

        if result:
          self.cursor.execute("DELETE FROM drinks WHERE date=?", (target_date,))
          self.conn.commit()
          print(f"Drinks deleted from date: {target_date}")
        else:
          print(f"No drinks from date: {target_date} .")
    elif choice == '2': # Week
      target_date = input("Enter a date within the week (YYYY-MM-DD) to clear entries for the entire week or leave empty to cancel: ")
      if not target_date:
        print("Operation canceled.")
        return
      else:
        start_of_week = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=datetime.strptime(target_date, "%Y-%m-%d").weekday())).strftime("%Y-%m-%d")
        end_of_week = (datetime.strptime(start_of_week, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
        self.cursor.execute('''DELETE FROM drinks
                            WHERE date BETWEEN ? AND ?''', (start_of_week, end_of_week))
        self.conn.commit()
        print(f"Drinks deleted from dates: {start_of_week} - {end_of_week}.")
    elif choice == '3': # All
      confirm = input("Are you sure you want to clear entries? (Type yes to confirm or leave empty to cancel): ")
      if not confirm:
        print("Operation canceled.")
        return
      else:
        if confirm.lower() == 'yes':
          self.cursor.execute("DELETE FROM drinks")
          self.conn.commit()
          print("All drinks removed")
        else:
          print("Operation canceled.")
    else:
      print("Invalid choice. Operation canceled.")
      
  # Fetches summary by current date
  def get_daily_summary(self):
    current_date = str(date.today())
    entries = self.cursor.execute("""
        SELECT id, type, ounces 
        FROM drinks 
        WHERE date=?
    """, (current_date,))
    
    total_ounces = 0
    formatted_entries = []

    for entry in entries:
        total_ounces += entry[2]
        formatted_entry = {
            'id': entry[0],
            'type': entry[1],
            'ounces': entry[2]
        }
        formatted_entries.append(formatted_entry)
      
    daily_goal = self.daily_goal

    goal_progress = total_ounces / daily_goal * 100 if daily_goal > 0 else 0

    daily_summary = {
        'date': current_date,
        'total_ounces': total_ounces,
        'daily_goal': daily_goal,
        'goal_progress': goal_progress,
        'entries': formatted_entries
    }

    return daily_summary
  
  # Fetches summary of current week      
  def get_weekly_summary(self):
    weekly_summary = {}
    total_weekly_ounces = 0
    current_date = date.today()

    start_of_week = current_date - timedelta(days=current_date.weekday())

    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_str = str(day_date)

        entries = self.cursor.execute("""
            SELECT id, type, ounces
            FROM drinks 
            WHERE date=?
            GROUP BY id, type
        """, (day_str,))

        formatted_entries = []
        total_ounces = 0

        for entry in entries:
            total_ounces += entry[2]
            formatted_entry = {
                'id': entry[0],
                'type': entry[1],
                'ounces': entry[2]
            }
            formatted_entries.append(formatted_entry)

        daily_goal = self.daily_goal
        goal_progress = total_ounces / daily_goal * 100 if daily_goal > 0 else 0

        weekly_summary[day_str] = {
            'date': day_str,
            'total_ounces': total_ounces,
            'daily_goal': daily_goal,
            'goal_progress': goal_progress,
            'entries': formatted_entries
        }

        total_weekly_ounces += total_ounces

    weekly_summary['total_weekly_ounces'] = total_weekly_ounces

    return weekly_summary

# Fetches summary by given date          
  def any_day_summary(self):
    target_date = input("Enter the date (YYYY-MM-DD) to view consumption for or leave empty to cancel: ")

    try:
      datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
      print("Invalid date format. Operation canceled.")
      return

    entries = self.cursor.execute("""
        SELECT id, type, ounces 
        FROM drinks 
        WHERE date=?
    """, (target_date,))
    
    total_ounces = 0
    formatted_entries = []

    for entry in entries:
        total_ounces += entry[2]
        formatted_entry = {
            'id': entry[0],
            'type': entry[1],
            'ounces': entry[2]
        }
        formatted_entries.append(formatted_entry)

    print(f"\nConsumption for {target_date}:")
    print(f"Total Ounces Consumed: {total_ounces} oz")

    if entries:
      for entry in entries:
        entry_type = entry.get('type', 'Unknown Type')
        entry_ounces = entry.get('ounces', 0)
        print(f"ID: {entry.doc_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
    else:
      print("No entries for the specified day.") 
    
    daily_goal = self.daily_goal

    goal_progress = total_ounces / daily_goal * 100 if daily_goal > 0 else 0  
      
    any_summary = {
      'date': target_date,
      'total_ounces': total_ounces,
      'daily_goal': daily_goal,
      'goal_progress': goal_progress,
      'entries': formatted_entries
  }

    return any_summary
  
  # Prints daily summary
  def print_daily_summary(self, daily_summary):
    current_date = datetime.strptime(daily_summary['date'], "%Y-%m-%d")
    formatted_date = current_date.strftime("%A, %B %d, %Y")
    print("\nSummary:")
    print(f"\nDate: {formatted_date}")
    print(f"Total Ounces Consumed: {daily_summary['total_ounces']} oz")
    print(f"Daily Goal: {daily_summary['daily_goal']} oz")
    print(f"Goal Progress: {daily_summary['goal_progress']:.2f}%")

    entries = daily_summary.get('entries', [])
    non_empty_entries = [entry for entry in entries if 'type' in entry and 'ounces' in entry]

    if non_empty_entries:
        print("\nEntries:")
        for entry in non_empty_entries:
            entry_id = entry.get('id', 'Unknown ID') 
            entry_type = entry.get('type', 'Unknown Type')
            entry_ounces = entry.get('ounces', 0)
            print(f"ID: {entry_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
    else:
        print("\nNo valid entries for the day.")
        
  # Prints weekly summary          
  def print_weekly_summary(self, weekly_summary):
    print("\nWeekly Summary:")
    for day_str, day_summary in weekly_summary.items():
        if day_str != 'total_weekly_ounces':
            day_date = datetime.strptime(day_str, "%Y-%m-%d")
            formatted_date = day_date.strftime("%A, %B %d, %Y")
            total_ounces = day_summary['total_ounces']
            entries = day_summary.get('entries', [])
            non_empty_entries = [entry for entry in entries if entry.get('type') and entry.get('ounces', 0) > 0]

            if non_empty_entries:
                print(f"\nDate: {formatted_date}")
                print(f"Total Ounces Consumed: {total_ounces} oz")
                print("\nEntries:")
                for entry in non_empty_entries:
                    entry_id = entry.get('id', 'Unknown ID')
                    entry_type = entry.get('type', 'Unknown Type')
                    entry_ounces = entry.get('ounces', 0)
                    print(f"ID: {entry_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
            else:
                print(f"\nNo valid entries for: {formatted_date}")

    print("\nTotal Ounces Consumed for the Week:", weekly_summary['total_weekly_ounces'])
  
  # Prints any summary
  def print_any_summary(self, any_summary):
    current_date = datetime.strptime(any_summary['date'], "%Y-%m-%d")
    formatted_date = current_date.strftime("%A, %B %d, %Y")
    print("\nDaily Summary:")
    print(f"\nDate: {formatted_date}")
    print(f"Total Ounces Consumed: {any_summary['total_ounces']} oz")
    print(f"Daily Goal: {any_summary['daily_goal']} oz")
    print(f"Goal Progress: {any_summary['goal_progress']:.2f}%")

    entries = any_summary.get('entries', [])
    non_empty_entries = [entry for entry in entries if 'type' in entry and 'ounces' in entry]

    if non_empty_entries:
        print("\nEntries:")
        for entry in non_empty_entries:
            entry_id = entry.get('id', 'Unknown ID')  # Fetch the ID
            entry_type = entry.get('type', 'Unknown Type')
            entry_ounces = entry.get('ounces', 0)
            print(f"ID: {entry_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
    else:
        print("\nNo valid entries for the day.")
  
  # Displays menu of options to user 
  def display_menu(self):
    while True:
      print("\nMenu:")
      print("1. Add Drink Entry")
      print("2. Add Previous Entry")
      print("3. Display Daily Summary")
      print("4. Display Weekly Summary")
      print("5. View Consumption for Any Day")
      print("6. Remove Drink Entry")
      print("7. Clear Multiple Entries")
      print("8. Create Backup")
      print("9. Exit")

      choice = input("Enter your choice (1-9): ")

      # Calls function based on user's choice
      if choice == '1':
        self.add_current_entry()
      elif choice == '2':
        self.add_previous_entry()
      elif choice == '3':
        daily_summary = self.get_daily_summary()
        self.print_daily_summary(daily_summary)
      elif choice == '4':
        weekly_summary = self.get_weekly_summary()
        self.print_weekly_summary(weekly_summary)
      elif choice == '5':
        any_summary = self.any_day_summary()
        self.print_any_summary(any_summary)
      elif choice == '6':
        summary = self.get_daily_summary()
        self.print_daily_summary(summary)
        self.remove_entry_id()
      elif choice == '7':
        self.remove_group_entry()
      elif choice == '8':
        self.backup_database()
      elif choice == '9':
        self.conn.close()
        break
      else:
        print("Invalid choice. Please enter a number between 1 and 9.")


water_tracker = WaterTracker()
water_tracker.display_menu()
