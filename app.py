import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO
import re
from db_config import db_settings

class Music:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Collection")
        self.root.geometry("1200x800")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Define colors
        self.colors = {
            'primary': '#2196F3',
            'secondary': '#607D8B',
            'background': '#F5F5F5',
            'surface': '#FFFFFF',
            'error': '#F44336',
            'text': '#212121',
            'text_secondary': '#757575'
        }
        
        # Configure styles
        self.configure_styles()
        
        # Initialize database
        try:
            self.db_config = db_settings
            self.db = mysql.connector.connect(**self.db_config)
            if self.db.is_connected():
                print("Database connected")
        except Error as e:
            print(f"Database error: {e}")
            self.db = None

        # Initialize variables
        self.current_user_id = None
        self.title_entry = None
        self.artist_entry = None
        self.format_var = tk.StringVar()
        self.date_entry = None
        self.cover_entry = None
        self.notes_text = None
        self.tree = None
        self.cover_label = None

        self.show_login_frame()

    def configure_styles(self):
        style = self.style
        colors = self.colors
        
        style.configure('Primary.TButton',
            background=colors['primary'],
            foreground='white',
            padding=(20, 10),
            font=('Helvetica', 10)
        )
        style.configure('Secondary.TButton',
            background=colors['secondary'],
            padding=(20, 10),
            font=('Helvetica', 10)
        )
        style.configure('Card.TFrame',
            background=colors['surface'],
            relief='flat'
        )
        style.configure('Title.TLabel',
            font=('Helvetica', 24, 'bold'),
            foreground=colors['text'],
            background=colors['surface']
        )
        style.configure('Header.TLabel',
            font=('Helvetica', 16),
            foreground=colors['text'],
            background=colors['surface']
        )
        style.configure('Modern.Treeview',
            background=colors['surface'],
            fieldbackground=colors['surface'],
            font=('Helvetica', 10)
        )
        style.configure('Modern.Treeview.Heading',
            font=('Helvetica', 12, 'bold')
        )

    def show_login_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = ttk.Frame(self.root, style='Card.TFrame')
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(main_frame, text="Music Collection", style='Title.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(main_frame, style='Card.TFrame')
        form_frame.pack(padx=40, pady=20)
        
        ttk.Label(form_frame, text="Username", style='Header.TLabel').pack(anchor='w', pady=(0, 5))
        self.username_entry = ttk.Entry(form_frame, width=30, font=('Helvetica', 12))
        self.username_entry.pack(pady=(0, 15), ipady=5)
        
        ttk.Label(form_frame, text="Password", style='Header.TLabel').pack(anchor='w', pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, show="•", width=30, font=('Helvetica', 12))
        self.password_entry.pack(pady=(0, 20), ipady=5)
        
        button_frame = ttk.Frame(form_frame, style='Card.TFrame')
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Login", style='Primary.TButton', command=self.login).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Register", style='Secondary.TButton', command=self.register).pack(side='left', padx=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            db = mysql.connector.connect(**self.db_config)
            cursor = db.cursor()
            
            cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            
            if result and result[1] == password:
                self.current_user_id = result[0]
                self.show_main_interface()
            else:
                messagebox.showerror("Error", "Invalid username or password")
                
            db.close()
        except Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
            db = mysql.connector.connect(**self.db_config)
            cursor = db.cursor()
            
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db.commit()
            db.close()
            
            messagebox.showinfo("Success", "Registration successful! Please login.")
        except Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def show_main_interface(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Left panel
        self.setup_left_panel(main_container)
        
        # Right panel
        self.setup_right_panel(main_container)
        
        # Load records
        self.load_records()

    def setup_left_panel(self, container):
        left_panel = ttk.Frame(container, style='Card.TFrame')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Search bar
        search_frame = ttk.Frame(left_panel, style='Card.TFrame')
        search_frame.pack(fill='x', pady=(0, 10))

        self.search_entry = ttk.Entry(search_frame, font=('Helvetica', 12))
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10), ipady=5)
        self.search_entry.bind('<KeyRelease>', self.search_records)

        self.sort_var = tk.StringVar()
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var,
                                 values=["Title", "Artist", "Date"],
                                 width=15, font=('Helvetica', 10))
        sort_combo.pack(side='right')
        sort_combo.set("Sort by")
        sort_combo.bind('<<ComboboxSelected>>', self.sort_records)

        # Records list
        self.tree = ttk.Treeview(left_panel, style='Modern.Treeview',
                                columns=("Title", "Artist", "Format", "Date"),
                                show="headings")
        
        for col in ("Title", "Artist", "Format", "Date"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.show_record_details)

        scrollbar = ttk.Scrollbar(left_panel, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

    def setup_right_panel(self, container):
        right_panel = ttk.Frame(container, style='Card.TFrame')
        right_panel.pack(side='right', fill='both', padx=(10, 0))

        ttk.Label(right_panel, text="Record Details", style='Title.TLabel').pack(pady=20)

        details_frame = ttk.Frame(right_panel, style='Card.TFrame')
        details_frame.pack(fill='x', padx=20)

        # Form fields
        ttk.Label(details_frame, text="Title", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        self.title_entry = ttk.Entry(details_frame, font=('Helvetica', 12))
        self.title_entry.pack(fill='x', pady=(0, 10))

        ttk.Label(details_frame, text="Artist", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        self.artist_entry = ttk.Entry(details_frame, font=('Helvetica', 12))
        self.artist_entry.pack(fill='x', pady=(0, 10))

        ttk.Label(details_frame, text="Format", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        format_combo = ttk.Combobox(details_frame, textvariable=self.format_var,
                                   values=["CD", "Vinyl"], font=('Helvetica', 12))
        format_combo.pack(fill='x', pady=(0, 10))

        ttk.Label(details_frame, text="Purchase Date", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        self.date_entry = ttk.Entry(details_frame, font=('Helvetica', 12))
        self.date_entry.pack(fill='x', pady=(0, 10))

        ttk.Label(details_frame, text="Cover URL", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        self.cover_entry = ttk.Entry(details_frame, font=('Helvetica', 12))
        self.cover_entry.pack(fill='x', pady=(0, 10))

        ttk.Label(details_frame, text="Notes", style='Header.TLabel').pack(anchor='w', pady=(10, 5))
        self.notes_text = tk.Text(details_frame, height=4, font=('Helvetica', 12))
        self.notes_text.pack(fill='x', pady=(0, 20))

        # Cover image
        self.cover_label = ttk.Label(details_frame)
        self.cover_label.pack(pady=10)

        # Buttons
        button_frame = ttk.Frame(details_frame, style='Card.TFrame')
        button_frame.pack(fill='x', pady=20)

        ttk.Button(button_frame, text="Add", style='Primary.TButton',
                  command=self.add_record).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Update", style='Secondary.TButton',
                  command=self.update_record).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete", style='Secondary.TButton',
                  command=self.delete_record).pack(side='left', padx=5)

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
    app = Music(root)
    #app.create_database()
    root.mainloop()
