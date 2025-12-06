import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from tkcalendar import Calendar

conn = sqlite3.connect('expense_tracker.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    amount REAL,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")
conn.commit()

LARGE_FONT = ("Arial", 16)
MEDIUM_FONT = ("Arial", 14)

def open_register_window():
    login_window.destroy()
    
    register_window = tk.Tk()
    register_window.title("Đăng ký")
    register_window.geometry("500x350")
    
    ttk.Label(register_window, text="Tên đăng nhập:", font=LARGE_FONT).grid(column=0, row=0, padx=20, pady=10, sticky="W")
    username_var = tk.StringVar()
    ttk.Entry(register_window, textvariable=username_var, font=MEDIUM_FONT).grid(column=1, row=0, padx=20, pady=10)
    
    ttk.Label(register_window, text="Mật khẩu:", font=LARGE_FONT).grid(column=0, row=1, padx=20, pady=10, sticky="W")
    password_var = tk.StringVar()
    ttk.Entry(register_window, textvariable=password_var, font=MEDIUM_FONT, show="*").grid(column=1, row=1, padx=20, pady=10)
    
    ttk.Label(register_window, text="Nhập lại mật khẩu:", font=LARGE_FONT).grid(column=0, row=2, padx=20, pady=10, sticky="W")
    confirm_password_var = tk.StringVar()
    ttk.Entry(register_window, textvariable=confirm_password_var, font=MEDIUM_FONT, show="*").grid(column=1, row=2, padx=20, pady=10)
    
    def register():
        username = username_var.get()
        password = password_var.get()
        confirm_password = confirm_password_var.get()
        
        if not username or not password or not confirm_password:
            messagebox.showerror("Lỗi đăng ký", "Tất cả các trường đều bắt buộc!")
            return
        
        if password != confirm_password:
            messagebox.showerror("Lỗi đăng ký", "Mật khẩu không khớp!")
            return
        
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Thành công", "Đăng ký thành công! Bạn có thể đăng nhập ngay.")
            register_window.destroy()
            open_login_window()
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi đăng ký", "Tên đăng nhập đã tồn tại!")
    
    ttk.Button(register_window, text="Đăng ký", command=register, style="Large.TButton").grid(column=0, row=3, columnspan=2, pady=20)
    
    login_label = tk.Label(register_window, text="Đã có tài khoản? Đăng nhập.", fg="blue", cursor="hand2", font=MEDIUM_FONT)
    login_label.grid(column=0, row=4, columnspan=2, pady=10)
    login_label.bind("<Button-1>", lambda e: open_login_window())
    
    register_window.mainloop()

def open_main_app():
    main_window = tk.Tk()
    main_window.title("Quản lý chi tiêu")
    main_window.geometry("650x800")

    def add_expense():
        description = desc_var.get()
        amount = amount_var.get()
        date = date_var.get()

        if description and amount and date:
            cursor.execute("INSERT INTO expenses (user_id, description, amount, date) VALUES (?, ?, ?, ?)",
                           (current_user_id, description, float(amount), date))
            conn.commit()
            refresh_expenses()
            desc_var.set("")
            amount_var.set("")
            date_var.set("")
        else:
            messagebox.showerror("Lỗi nhập liệu", "Tất cả các trường đều bắt buộc!")

    def refresh_expenses():
        for row in expenses_tree.get_children():
            expenses_tree.delete(row)
        
        cursor.execute("SELECT description, amount, date FROM expenses WHERE user_id = ?", (current_user_id,))
        for row in cursor.fetchall():
            expenses_tree.insert('', 'end', values=row)

    def logout():
        main_window.destroy()
        open_login_window()

    ttk.Label(main_window, text="Mô tả:", font=LARGE_FONT).grid(column=0, row=0, padx=20, pady=10, sticky="W")
    desc_var = tk.StringVar()
    ttk.Entry(main_window, textvariable=desc_var, font=MEDIUM_FONT).grid(column=1, row=0, padx=20, pady=10)

    ttk.Label(main_window, text="Số tiền:", font=LARGE_FONT).grid(column=0, row=1, padx=20, pady=10, sticky="W")
    amount_var = tk.StringVar()
    ttk.Entry(main_window, textvariable=amount_var, font=MEDIUM_FONT).grid(column=1, row=1, padx=20, pady=10)

    ttk.Label(main_window, text="Ngày:", font=LARGE_FONT).grid(column=0, row=2, padx=20, pady=10, sticky="W")
    date_var = tk.StringVar()
    calendar = Calendar(main_window, selectmode='day', date_pattern='yyyy-mm-dd', font=MEDIUM_FONT)
    calendar.grid(column=1, row=2, padx=20, pady=10)
    
    def update_date():
        date_var.set(calendar.get_date())

    calendar.bind("<<CalendarSelected>>", lambda e: update_date())

    ttk.Button(main_window, text="Thêm chi tiêu", command=add_expense, style="Large.TButton").grid(column=0, row=3, columnspan=2, pady=20)

    ttk.Button(main_window, text="Đăng xuất", command=logout, style="Large.TButton").grid(column=0, row=5, columnspan=2, pady=20)

    expenses_tree = ttk.Treeview(main_window, columns=("Mô tả", "Số tiền", "Ngày"), show="headings")
    expenses_tree.heading("Mô tả", text="Mô tả")
    expenses_tree.heading("Số tiền", text="Số tiền")
    expenses_tree.heading("Ngày", text="Ngày")
    expenses_tree.grid(column=0, row=4, columnspan=2, padx=20, pady=10)

    refresh_expenses()
    main_window.mainloop()

def open_login_window():
    global login_window
    login_window = tk.Tk()
    login_window.title("Đăng nhập")
    login_window.geometry("500x300")
    
    ttk.Label(login_window, text="Tên đăng nhập:", font=LARGE_FONT).grid(column=0, row=0, padx=20, pady=10, sticky="W")
    username_var = tk.StringVar()
    ttk.Entry(login_window, textvariable=username_var, font=MEDIUM_FONT).grid(column=1, row=0, padx=20, pady=10)
    
    ttk.Label(login_window, text="Mật khẩu:", font=LARGE_FONT).grid(column=0, row=1, padx=20, pady=10, sticky="W")
    password_var = tk.StringVar()
    ttk.Entry(login_window, textvariable=password_var, font=MEDIUM_FONT, show="*").grid(column=1, row=1, padx=20, pady=10)
    
    def login():
        username = username_var.get()
        password = password_var.get()
        
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            global current_user_id
            current_user_id = user[0]
            login_window.destroy()
            open_main_app()
        else:
            messagebox.showerror("Lỗi đăng nhập", "Tên đăng nhập hoặc mật khẩu không đúng")
    
    ttk.Button(login_window, text="Đăng nhập", command=login, style="Large.TButton").grid(column=0, row=2, columnspan=2, pady=20)
    
    register_label = tk.Label(login_window, text="Chưa có tài khoản? Đăng ký.", fg="blue", cursor="hand2", font=MEDIUM_FONT)
    register_label.grid(column=0, row=3, columnspan=2, pady=10)
    register_label.bind("<Button-1>", lambda e: open_register_window())
    
    login_window.mainloop()

style = ttk.Style()
style.configure("Large.TButton", font=LARGE_FONT, padding=10)

current_user_id = None

open_login_window()
