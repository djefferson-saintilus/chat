import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
from PIL import Image, ImageTk
import os

# Initialize the main application window
app = tk.Tk()
app.title("User Login App")
app.geometry("400x500")
app.config(bg="#e8f0f2")

current_user = None
profile_image_label = None  # Global variable to hold the label for profile picture

# Function to setup the SQLite database
def setup_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        profile_picture TEXT DEFAULT 'default_icon.png',
        bio TEXT DEFAULT '',
        friends TEXT DEFAULT '',
        online_status INTEGER DEFAULT 0
    )
    """)
    
    # Create notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0
    )
    """)
    
    # Create friend requests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        status TEXT DEFAULT 'pending'  -- 'pending', 'accepted', 'declined'
    )
    """)

    conn.commit()
    conn.close()

# Function to create a new account
def create_account():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning("Warning", "Please enter both username and password.")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
    
    conn.close()

# Function to login
def login():
    global current_user
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    
    if cursor.fetchone():
        current_user = username
        app.withdraw()
        open_profile_window()
    else:
        messagebox.showerror("Error", "Invalid username or password.")
    
    conn.close()

# Function to open the profile window
def open_profile_window():
    profile_window = tk.Toplevel(app)
    profile_window.title("User Profile")
    profile_window.geometry("400x600")
    profile_window.config(bg="#e8f0f2")

    global profile_image_label  # Make it global to modify it later

    # Profile picture section
    profile_picture_label = tk.Label(profile_window, text="Profile Picture:", font=("Arial", 12, 'bold'), bg="#e8f0f2")
    profile_picture_label.pack(pady=10)

    # Label to display profile picture
    profile_image_label = tk.Label(profile_window)
    profile_image_label.pack(pady=5)

    def upload_picture():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            # Save the profile picture path to the database
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET profile_picture = ? WHERE username = ?", (file_path, current_user))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Profile picture updated!")
            display_profile_picture(file_path)  # Display the new profile picture

    upload_button = tk.Button(profile_window, text="Upload Picture", command=upload_picture, bg="#4CAF50", fg="white", font=("Arial", 10, 'bold'))
    upload_button.pack(pady=5)

    # Function to display the profile picture
    def display_profile_picture(image_path):
        try:
            # Open image using Pillow
            img = Image.open(image_path)
            img = img.resize((100, 100), Image.LANCZOS)  # Use LANCZOS for high-quality downsampling
            img = ImageTk.PhotoImage(img)
            profile_image_label.config(image=img)
            profile_image_label.image = img  # Keep a reference to avoid garbage collection
        except Exception as e:
            print("Error loading image:", e)
            profile_image_label.config(text="Failed to load image")

    # Load existing profile picture
    def load_profile_picture():
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT profile_picture FROM users WHERE username = ?", (current_user,))
        profile_picture = cursor.fetchone()[0]
        conn.close()
        display_profile_picture(profile_picture)

    load_profile_picture()  # Load and display the profile picture when the profile window opens

    # Bio/About Me section
    bio_label = tk.Label(profile_window, text="Bio/About Me:", font=("Arial", 12, 'bold'), bg="#e8f0f2")
    bio_label.pack()
    bio_entry = tk.Text(profile_window, height=5, width=40, font=("Arial", 12))
    bio_entry.pack(pady=5)

    def load_bio():
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT bio FROM users WHERE username = ?", (current_user,))
        bio_text = cursor.fetchone()[0]
        conn.close()
        bio_entry.insert("1.0", bio_text)

    def save_bio():
        bio_text = bio_entry.get("1.0", tk.END).strip()
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET bio = ? WHERE username = ?", (bio_text, current_user))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Bio updated successfully!")

    load_bio()
    save_bio_button = tk.Button(profile_window, text="Save Bio", font=("Arial", 10), command=save_bio, bg="#2196F3", fg="white")
    save_bio_button.pack(pady=5)

    # Notification label
    notification_label = tk.Label(profile_window, text="Notifications:", font=("Arial", 12, 'bold'), bg="#e8f0f2")
    notification_label.pack(pady=10)

    def load_notifications():
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Load notifications for messages
        cursor.execute("SELECT message FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
        notifications = cursor.fetchall()

        # Load friend requests
        cursor.execute("SELECT sender FROM friend_requests WHERE receiver = ? AND status = 'pending'", (current_user,))
        friend_requests = cursor.fetchall()
        conn.close()

        # Prepare display text for notifications
        notification_text = "New Messages:\n"
        if notifications:
            messages = [msg[0] for msg in notifications]
            notification_text += "\n".join(messages)
        else:
            notification_text += "No new messages."

        notification_text += "\n\nFriend Requests:\n"
        if friend_requests:
            request_senders = [req[0] for req in friend_requests]
            notification_text += "\n".join(request_senders)
        else:
            notification_text += "No new friend requests."

        notification_label.config(text=notification_text)

    # Refresh button
    refresh_button = tk.Button(profile_window, text="Refresh", command=load_notifications, bg="#FFC107", fg="black", font=("Arial", 10, 'bold'))
    refresh_button.pack(pady=10)

    def auto_refresh_notifications():
        load_notifications()  # Refresh notifications
        profile_window.after(5000, auto_refresh_notifications)  # Call this function again after 5000 ms (5 seconds)

    auto_refresh_notifications()  # Start the auto-refresh process when the profile window opens

    # Friend search bar
    search_label = tk.Label(profile_window, text="Search for Friends:", font=("Arial", 12, 'bold'), bg="#e8f0f2")
    search_label.pack(pady=10)
    search_entry = tk.Entry(profile_window, font=("Arial", 12), width=30)
    search_entry.pack()

    def send_friend_request():
        friend_username = search_entry.get().strip()
        if not friend_username:
            messagebox.showwarning("Warning", "Please enter a username to send a friend request.")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (friend_username,))
        if cursor.fetchone():
            cursor.execute("INSERT INTO friend_requests (sender, receiver) VALUES (?, ?)", (current_user, friend_username))
            conn.commit()
            messagebox.showinfo("Success", "Friend request sent!")
        else:
            messagebox.showwarning("Warning", "User not found.")

        conn.close()

    send_request_button = tk.Button(profile_window, text="Send Friend Request", command=send_friend_request, bg="#2196F3", fg="white", font=("Arial", 10, 'bold'))
    send_request_button.pack(pady=5)

    # Online Friends Count
    online_count_label = tk.Label(profile_window, text="Online Friends Count: 0", font=("Arial", 12), bg="#e8f0f2")
    online_count_label.pack(pady=10)

    # Logout button
    logout_button = tk.Button(profile_window, text="Logout", command=lambda: [profile_window.destroy(), app.deiconify()], bg="#f44336", fg="white", font=("Arial", 12, 'bold'))
    logout_button.pack(pady=20)

    # Load the number of online friends (for demonstration, setting it to 0)
    def load_online_count():
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE online_status = 1")
        count = cursor.fetchone()[0]
        conn.close()
        online_count_label.config(text=f"Online Friends Count: {count}")

    load_online_count()

# Set up the database
setup_database()

# Create the login UI elements
username_label = tk.Label(app, text="Username:", bg="#e8f0f2", font=("Arial", 12))
username_label.pack(pady=10)
username_entry = tk.Entry(app, font=("Arial", 12))
username_entry.pack(pady=5)

password_label = tk.Label(app, text="Password:", bg="#e8f0f2", font=("Arial", 12))
password_label.pack(pady=10)
password_entry = tk.Entry(app, show='*', font=("Arial", 12))
password_entry.pack(pady=5)

# Login button
login_button = tk.Button(app, text="Login", command=login, bg="#4CAF50", fg="white", font=("Arial", 12, 'bold'))
login_button.pack(pady=20)

# Create account section
create_account_label = tk.Label(app, text="Don't have an account?", bg="#e8f0f2")
create_account_label.pack(pady=5)

create_account_button = tk.Button(app, text="Create Account", command=create_account, bg="#2196F3", fg="white", font=("Arial", 12, 'bold'))
create_account_button.pack(pady=5)

# Start the application
app.mainloop()
