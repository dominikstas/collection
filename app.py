import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO
import re

class MusicCollectionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Collection Manager")
        self.root.geometry("1200x800")
        
        # Database connection
        self.db_config = {
            'host': 'localhost',
            'user': '',
            'password': '',
            'database': 'music_collection'
        }
        
        # Initialize login frame
        self.show_login_frame()
        
    def create_database(self):
        try:
            conn = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            cursor = conn.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")
            
            # Use the database
            cursor.execute(f"USE {self.db_config['database']}")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)
            
            # Create records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    title VARCHAR(255) NOT NULL,
                    artist VARCHAR(255) NOT NULL,
                    format ENUM('CD', 'Vinyl') NOT NULL,
                    purchase_date DATE,
                    cover_url TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def show_login_frame(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create login frame
        login_frame = ttk.Frame(self.root, padding="20")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Login widgets
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, pady=5)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)
        
        ttk.Button(login_frame, text="Login", command=self.login).grid(row=2, column=0, pady=10)
        ttk.Button(login_frame, text="Register", command=self.register).grid(row=2, column=1, pady=10)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            
            if result and result[1] == password:  # In production, use proper password hashing
                self.current_user_id = result[0]
                self.show_main_interface()
            else:
                messagebox.showerror("Error", "Invalid username or password")
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Registration successful! Please login.")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def show_main_interface(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create main interface
        # Left panel for record list
        left_panel = ttk.Frame(self.root, padding="10")
        left_panel.pack(side="left", fill="both", expand=True)
        
        # Search frame
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_records)
        
        # Sort frame
        sort_frame = ttk.Frame(left_panel)
        sort_frame.pack(fill="x", pady=5)
        
        ttk.Label(sort_frame, text="Sort by:").pack(side="left")
        self.sort_var = tk.StringVar()
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, 
                                 values=["Title", "Artist", "Purchase Date"])
        sort_combo.pack(side="left", padx=5)
        sort_combo.bind('<<ComboboxSelected>>', self.sort_records)
        
        # Records treeview
        columns = ("Title", "Artist", "Format", "Purchase Date")
        self.tree = ttk.Treeview(left_panel, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        self.tree.pack(fill="both", expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.show_record_details)
        
        # Right panel for record details
        right_panel = ttk.Frame(self.root, padding="10")
        right_panel.pack(side="right", fill="both")
        
        # Record details form
        ttk.Label(right_panel, text="Title:").grid(row=0, column=0, pady=5)
        self.title_entry = ttk.Entry(right_panel)
        self.title_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(right_panel, text="Artist:").grid(row=1, column=0, pady=5)
        self.artist_entry = ttk.Entry(right_panel)
        self.artist_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(right_panel, text="Format:").grid(row=2, column=0, pady=5)
        self.format_var = tk.StringVar()
        format_combo = ttk.Combobox(right_panel, textvariable=self.format_var, 
                                   values=["CD", "Vinyl"])
        format_combo.grid(row=2, column=1, pady=5)
        
        ttk.Label(right_panel, text="Purchase Date:").grid(row=3, column=0, pady=5)
        self.date_entry = ttk.Entry(right_panel)
        self.date_entry.grid(row=3, column=1, pady=5)
        
        ttk.Label(right_panel, text="Cover URL:").grid(row=4, column=0, pady=5)
        self.cover_entry = ttk.Entry(right_panel)
        self.cover_entry.grid(row=4, column=1, pady=5)
        
        ttk.Label(right_panel, text="Notes:").grid(row=5, column=0, pady=5)
        self.notes_text = tk.Text(right_panel, height=4, width=30)
        self.notes_text.grid(row=5, column=1, pady=5)
        
        # Cover image label
        self.cover_label = ttk.Label(right_panel)
        self.cover_label.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(right_panel)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add New", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Update", command=self.update_record).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_record).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_form).pack(side="left", padx=5)
        
        # Load initial records
        self.load_records()
    
    def load_records(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, artist, format, purchase_date 
                FROM records 
                WHERE user_id = %s
                ORDER BY title
            """, (self.current_user_id,))
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Insert records
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def search_records(self, event=None):
        search_term = self.search_entry.get().lower()
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, artist, format, purchase_date 
                FROM records 
                WHERE user_id = %s 
                AND (LOWER(title) LIKE %s OR LOWER(artist) LIKE %s)
                ORDER BY title
            """, (self.current_user_id, f"%{search_term}%", f"%{search_term}%"))
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Insert filtered records
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def sort_records(self, event=None):
        sort_field = self.sort_var.get()
        field_map = {
            "Title": "title",
            "Artist": "artist",
            "Purchase Date": "purchase_date"
        }
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT title, artist, format, purchase_date 
                FROM records 
                WHERE user_id = %s 
                ORDER BY {field_map[sort_field]}
            """, (self.current_user_id,))
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Insert sorted records
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def show_record_details(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, artist, format, purchase_date, cover_url, notes
                FROM records 
                WHERE user_id = %s AND title = %s
            """, (self.current_user_id, self.tree.item(selected_item[0])['values'][0]))
            
            record = cursor.fetchone()
            if record:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, record[0])
                
                self.artist_entry.delete(0, tk.END)
                self.artist_entry.insert(0, record[1])
                
                self.format_var.set(record[2])
                
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, record[3])
                
                self.cover_entry.delete(0, tk.END)
                self.cover_entry.insert(0, record[4] or "")
                
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", record[5] or "")
                
                # Load cover image
                self.load_cover_image(record[4])
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def load_cover_image(self, url):
        if not url:
            self.cover_label.configure(image="")
            return
            
        try:
            response = urllib.request.urlopen(url)
            image_data = response.read()
            image = Image.open(BytesIO(image_data))
            
            # Resize image to fit
            image.thumbnail((200, 200))
            
            photo = ImageTk.PhotoImage(image)
            self.cover_label.configure(image=photo)
            self.cover_label.image = photo  # Keep a reference
            
        except Exception as e:
            messagebox.showerror("Image Error", f"Error loading image: {e}")
            self.cover_label.configure(image="")
    
    def add_record(self):
        if not self.validate_form():
            return
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO records 
                (user_id, title, artist, format, purchase_date, cover_url, notes)
                VALUES (%            """, (self.current_user_id,))
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Insert sorted records
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)
                
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def show_record_details(self, event=None):
        selected_item = self.tree.selection()
        if selected_item:
            record_values = self.tree.item(selected_item, "values")
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, record_values[0])
            self.artist_entry.delete(0, tk.END)
            self.artist_entry.insert(0, record_values[1])
            self.format_var.set(record_values[2])
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, record_values[3])
    
    def add_record(self):
        title = self.title_entry.get()
        artist = self.artist_entry.get()
        record_format = self.format_var.get()
        purchase_date = self.date_entry.get()
        cover_url = self.cover_entry.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        if not title or not artist or not record_format:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO records (user_id, title, artist, format, purchase_date, cover_url, notes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.current_user_id, title, artist, record_format, purchase_date, cover_url, notes))
            
            conn.commit()
            conn.close()
            
            self.load_records()
            self.clear_form()
            messagebox.showinfo("Success", "Record added successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def update_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No record selected to update.")
            return
        
        title = self.title_entry.get()
        artist = self.artist_entry.get()
        record_format = self.format_var.get()
        purchase_date = self.date_entry.get()
        cover_url = self.cover_entry.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            record_id = self.tree.item(selected_item, "values")[0]
            
            cursor.execute("""
                UPDATE records
                SET title = %s, artist = %s, format = %s, purchase_date = %s, cover_url = %s, notes = %s
                WHERE id = %s AND user_id = %s
            """, (title, artist, record_format, purchase_date, cover_url, notes, record_id, self.current_user_id))
            
            conn.commit()
            conn.close()
            
            self.load_records()
            self.clear_form()
            messagebox.showinfo("Success", "Record updated successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def delete_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No record selected to delete.")
            return
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            record_id = self.tree.item(selected_item, "values")[0]
            
            cursor.execute("DELETE FROM records WHERE id = %s AND user_id = %s", (record_id, self.current_user_id))
            
            conn.commit()
            conn.close()
            
            self.load_records()
            self.clear_form()
            messagebox.showinfo("Success", "Record deleted successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
    
    def clear_form(self):
        self.title_entry.delete(0, tk.END)
        self.artist_entry.delete(0, tk.END)
        self.format_var.set("")
        self.date_entry.delete(0, tk.END)
        self.cover_entry.delete(0, tk.END)
        self.notes_text.delete("1.0", tk.END)
        self.cover_label.configure(image="")

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicCollectionManager(root)
    app.create_database()
    root.mainloop()
