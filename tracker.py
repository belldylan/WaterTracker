from datetime import date, timedelta, datetime
from tinydb import TinyDB, Query
import shutil
Fetch = Query()

class WaterTracker:
  daily_goal = 68  
  
  # Creates/Opens database file
  def __init__(self, db_file='db.json'):
      self.db = TinyDB(db_file)

  # Checks for empty inputs
  def get_non_empty_input(self, prompt):
    value = input(prompt)

    while not value.strip():
      self.display_menu()
        
    return value if value.strip() else None
  
  # Creates a backup by copying the current database file
  def backup_database(self, backup_file='backup.json'):
    try:
      shutil.copy('db.json', backup_file)
      print(f"Backup created successfully: {backup_file}")
    except FileNotFoundError:
      print("Error: Database file not found. Make sure the database file exists.")

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
    
    entry = {
      'date': target_date,
      'type': drink_type,
      'ounces': ounces_consumed
    }

    entry = {key: entry.get(key, None) for key in ['date', 'type', 'ounces']}
    self.db.insert(entry)
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
    ounces_consumed = float(ounces_consumed)
    
    if not ounces_consumed:
      print("Operation canceled.")
      return

    entry = {
    'date': target_date,
    'type': drink_type,
    'ounces': ounces_consumed
    }

    entry = {key: entry.get(key, None) for key in ['date', 'type', 'ounces']}
    self.db.insert(entry)
    print(f"Entry added for {target_date}: {ounces_consumed} ounces of {drink_type}.")
    
  # Removes entry by id  
  def remove_entry_id(self, entry_id):
    try:
      entry_id = int(entry_id)
    except ValueError:
      print("Invalid entry ID. Operation canceled.")
      return

    self.db.remove(doc_ids=[entry_id])
    print(f"Entry with ID {entry_id} removed successfully.")
    
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

    if choice == '1':
      target_date = input("Enter the date (YYYY-MM-DD) to clear entries for or leave empty to cancel: ")
      if not target_date:
        print("Operation canceled.")
        return
      else:
        self.db.remove(Fetch.date == target_date)
    elif choice == '2':
      target_date = input("Enter a date within the week (YYYY-MM-DD) to clear entries for the entire week or leave empty to cancel: ")
      if not target_date:
        print("Operation canceled.")
        return
      else:
        start_of_week = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=datetime.strptime(target_date, "%Y-%m-%d").weekday())
        end_of_week = start_of_week + timedelta(days=6)
        self.db.remove((Fetch.date >= start_of_week.strftime("%Y-%m-%d")) & (Fetch.date <= end_of_week.strftime("%Y-%m-%d")))
    elif choice == '3':
      confirm = input("Are you sure you want to clear entries? (yes/no or leave empty to cancel): ")
      if not confirm:
        print("Operation canceled.")
        return
      else:
        if confirm.lower() == 'yes':
          self.db.truncate()
        else:
          print("Operation canceled.")
    else:
      print("Invalid choice. Operation canceled.")
  
  # Fetches summary by given date          
  def any_day_summary(self):
    target_date = input("Enter the date (YYYY-MM-DD) to view consumption for or leave empty to cancel: ")

    try:
      datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
      print("Invalid date format. Operation canceled.")
      return

    entries = self.db.search(Fetch.date == target_date)

    # Ensure 'ounces' key exists in all entries and replace None with 0
    for entry in entries:
      entry['ounces'] = entry.get('ounces', 0)

    # Display the consumption for the specified day
    total_ounces = sum(entry['ounces'] for entry in entries)

    print(f"\nConsumption for {target_date}:")
    print(f"Total Ounces Consumed: {total_ounces} oz")

    if entries:
      print("\nEntries:")
      for entry in entries:
        entry_type = entry.get('type', 'Unknown Type')
        entry_ounces = entry.get('ounces', 0)
        print(f"ID: {entry.doc_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
    else:
      print("No entries for the specified day.") 
             
  # Fetches summary by current date
  def get_daily_summary(self):
    current_date = str(date.today())
    entries = self.db.search(Fetch.date == current_date)

    for entry in entries:
      entry['ounces'] = entry.get('ounces', 0)

    total_ounces = sum(entry['ounces'] for entry in entries)
    daily_goal = self.daily_goal

    goal_progress = total_ounces / daily_goal * 100 if daily_goal > 0 else 0

    return {
      'date': current_date,
      'total_ounces': total_ounces,
      'daily_goal': daily_goal,
      'goal_progress': goal_progress,
      'entries': entries
    }
  
  # Fetches summary of current week      
  def get_weekly_summary(self):
    weekly_summary = {}
    total_weekly_ounces = 0
    current_date = date.today()

    start_of_week = current_date - timedelta(days=current_date.weekday())

    for i in range(7):
      day_date = start_of_week + timedelta(days=i)
      day_str = str(day_date)

      entries = self.db.search(Fetch.date == day_str)

      for entry in entries:
        entry['ounces'] = entry.get('ounces', 0)

      total_ounces = sum(entry['ounces'] for entry in entries)

      weekly_summary[day_str] = {
        'total_ounces': total_ounces,
        'entries': entries
      }

      total_weekly_ounces += total_ounces

    weekly_summary['total_weekly_ounces'] = total_weekly_ounces

    return weekly_summary

  # Prints daily summary
  def print_daily_summary(self, summary):
    current_date = datetime.strptime(summary['date'], "%Y-%m-%d")
    formatted_date = current_date.strftime("%A, %B %d, %Y")
    print("\nDaily Summary:")
    print(f"\nDate: {formatted_date}")
    print(f"Total Ounces Consumed: {summary['total_ounces']} oz")
    print(f"Daily Goal: {summary['daily_goal']} oz")
    print(f"Goal Progress: {summary['goal_progress']:.2f}%")

    entries = summary.get('entries', [])
    non_empty_entries = [entry for entry in entries if entry.get('type') and entry.get('ounces', 0) > 0]

    if non_empty_entries:
      print("\nEntries:")
      for entry in non_empty_entries:
        entry_type = entry.get('type', 'Unknown Type')
        entry_ounces = entry.get('ounces', 0)
        print(f"ID: {entry.doc_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
    else:
      print("\nNo valid entries for the day.")
  
  # Prints weekly summary          
  def print_weekly_summary(self, weekly_summary):
    print("\nWeekly Summary:")
    for day_str, day_summary in weekly_summary.items():
      if day_str != 'total_weekly_ounces':
        day_date = datetime.strptime(day_str, "%Y-%m-%d")
        formatted_date = day_date.strftime("%A, %B %d, %Y")
        entries = day_summary.get('entries', [])
        non_empty_entries = [entry for entry in entries if entry.get('type') and entry.get('ounces', 0) > 0]
        
        if non_empty_entries:
          print(f"\nDate: {formatted_date}")
          print(f"Total Ounces Consumed: {day_summary['total_ounces']} oz")
          print("\nEntries:")
          for entry in non_empty_entries:
            entry_type = entry.get('type', 'Unknown Type')
            entry_ounces = entry.get('ounces', 0)
            print(f"ID: {entry.doc_id}, Type: {entry_type}, Ounces: {entry_ounces} oz")
        else:
          print(f"\nNo valid entries for: {formatted_date}")

    print("\nTotal Ounces Consumed for the Week:", weekly_summary['total_weekly_ounces'])
  
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
      print("7. Clear All Entries")
      print("8. Create Backup")
      print("9. Exit")

      choice = input("Enter your choice (1-9): ")

      # Calls function based on user's choice
      if choice == '1':
        self.add_current_entry()
      elif choice == '2':
        self.add_previous_entry()
      elif choice == '3':
        summary = self.get_daily_summary()
        self.print_daily_summary(summary)
      elif choice == '4':
        weekly_summary = self.get_weekly_summary()
        self.print_weekly_summary(weekly_summary)
      elif choice == '5':
        self.any_day_summary()
      elif choice == '6':
        summary = self.get_daily_summary()
        self.print_daily_summary(summary)
        entry_id = input("Enter the ID of the entry to remove (or leave empty to cancel): ")
        if entry_id:
          self.remove_entry_id(int(entry_id))
      elif choice == '7':
        self.remove_group_entry()
      elif choice == '8':
        self.backup_database()
      elif choice == '9':
        break
      else:
        print("Invalid choice. Please enter a number between 1 and 9.")


water_tracker = WaterTracker()
water_tracker.display_menu()
