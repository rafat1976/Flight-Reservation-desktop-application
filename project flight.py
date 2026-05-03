import tkinter as tk
from tkinter import Tk, Label, Button, Entry, ttk, messagebox
import pyodbc
import re
from tkcalendar import DateEntry
from datetime import date, datetime
import random

# ========================================================
#             SMART DATABASE CONNECTION
# ========================================================
def create_connection():
    try:
        available_drivers = pyodbc.drivers()
    except Exception:
        available_drivers = []

    driver_name = '{SQL Server}' # ডিফল্ট
    if 'ODBC Driver 17 for SQL Server' in available_drivers:
        driver_name = '{ODBC Driver 17 for SQL Server}'
    elif 'SQL Server Native Client 11.0' in available_drivers:
        driver_name = '{SQL Server Native Client 11.0}'

    try:
        conn = pyodbc.connect(
            f'Driver={driver_name};'
            r'Server=.;'                
            r'Database=FRS;'
            r'Trusted_Connection=yes;'
            r'TrustServerCertificate=yes;'
        )
        return conn
    except pyodbc.Error as ex:
        root_err = Tk()
        root_err.withdraw()
        messagebox.showerror("Database Connection Error", f"Connection Failed.\n\nDetails:\n{ex}")
        exit()

# গ্লোবাল কানেকশন অবজেক্ট
connection = create_connection()
cursor = connection.cursor()
print("Database Connected Successfully!")

# --- Configuration: Colors & Fonts ---
NEW_BG_COLOR = '#0066ff'
NEW_FG_COLOR = '#FFFFFF'
BASE_FONT_FAMILY = 'Segoe UI'

def go_back(current_window):
    current_window.destroy()
    create_main_menu()

def go_to_login(current_window):
    current_window.destroy()
    create_login_window()

# ========================================================
#           LOGIC: HARDCODED BANGLADESHI PLACES & CLASSES
# ========================================================
def get_places():
    return [
        "Dhaka", "Cox's Bazar", "Chittagong", 
        "Sylhet", "Rajshahi", "Jessore", 
        "Saidpur", "Barisal"
    ]

def get_classes():
    return ["Economy", "Business"]

# ========================================================
#           WINDOW: SEARCH RESULTS (TREEVIEW)
# ========================================================
def show_search_results(results):
    root2 = Tk()
    root2.title("AVAILABLE FLIGHTS")
    root2.geometry('900x500')
    root2['background'] = NEW_BG_COLOR

    Label(root2, text="Available Flights", font=(BASE_FONT_FAMILY, 24, 'bold'), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).pack(pady=10)
    Label(root2, text="Select a flight and click 'Proceed to Booking'.", font=(BASE_FONT_FAMILY, 12, 'italic'), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).pack()

    tree_frame = tk.Frame(root2)
    tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    columns = ("FlightName", "Departure", "Arrival", "Source", "Destination", "Day", "Date", "Price")
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=tree_scroll.set)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor=tk.CENTER)

    tree.pack(fill=tk.BOTH, expand=True)
    tree_scroll.config(command=tree.yview)

    if results:
        for flight in results:
            tree.insert('', tk.END, values=flight)

    def book_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a flight first.", parent=root2)
            return
        
        values = tree.item(selected, 'values')
        flight_data = {
            "name": values[0], "dep": values[1], "arr": values[2],
            "source": values[3], "dest": values[4], "day": values[5], "date": values[6], "price": values[7]
        }
        root2.destroy()
        booking_window(flight_data)

    btn_frame = tk.Frame(root2, bg=NEW_BG_COLOR)
    btn_frame.pack(pady=20)

    Button(btn_frame, text="Proceed to Booking", font=(BASE_FONT_FAMILY, 10, 'bold'), width=20, command=book_selected).pack(side=tk.LEFT, padx=10)
    Button(btn_frame, text="Back", font=(BASE_FONT_FAMILY, 10, 'bold'), width=15, command=lambda: go_back(root2)).pack(side=tk.LEFT, padx=10)

    root2.mainloop()

# ========================================================
#           WINDOW: SEARCH FLIGHT (SMART DATABASE QUERY)
# ========================================================
def search_window():
    root1 = Tk()
    root1.title("SEARCH FLIGHT")
    root1.geometry('500x450')
    root1['background'] = NEW_BG_COLOR

    Label(root1, text="Search Flight", font=(BASE_FONT_FAMILY, 24, 'bold'), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).pack(pady=20)

    f = tk.Frame(root1, bg=NEW_BG_COLOR)
    f.pack(pady=10)

    Label(f, text="From:", font=(BASE_FONT_FAMILY, 12), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=0, column=0, padx=10, pady=5)
    src = ttk.Combobox(f, values=get_places(), state='readonly', width=25)
    src.grid(row=0, column=1)

    Label(f, text="To:", font=(BASE_FONT_FAMILY, 12), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=1, column=0, padx=10, pady=5)
    dest = ttk.Combobox(f, values=get_places(), state='readonly', width=25)
    dest.grid(row=1, column=1)

    Label(f, text="Date:", font=(BASE_FONT_FAMILY, 12), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=2, column=0, padx=10, pady=5)
    
    cal = DateEntry(f, width=23, date_pattern='y-mm-dd', 
                    background='darkblue', foreground='white', borderwidth=2,
                    year=2026, mindate=date(2026, 1, 1), maxdate=date(2026, 12, 31)) 
    cal.grid(row=2, column=1)

    def search_function():
        s, d, date_val = src.get(), dest.get(), str(cal.get_date())

        if not s or not d:
            messagebox.showerror("Error", "Select source and destination.", parent=root1)
            return
        if s == d:
            messagebox.showerror("Error", "Source and Destination cannot be same.", parent=root1)
            return

        try:
            dt = datetime.strptime(date_val, '%Y-%m-%d')
            day_name = dt.strftime('%A')

            query = "SELECT FlightName, Dep_time, Arr_time, Source, Destination, Price FROM Flight WHERE Source=? AND Destination=?"
            cursor.execute(query, (s, d))
            rows = cursor.fetchall()

            if rows:
                results = []
                for r in rows:
                    fake_row = (r[0], r[1], r[2], r[3], r[4], day_name, date_val, r[5])
                    results.append(fake_row)

                root1.destroy()
                show_search_results(results) 
            else:
                messagebox.showwarning("Not Found", "No flights available for this route.", parent=root1)

        except pyodbc.Error as ex:
            messagebox.showerror("Database Error", str(ex), parent=root1)

    tk.Button(root1, text="Search", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=search_function).pack(pady=20)
    tk.Button(root1, text="Back", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=lambda: go_back(root1)).pack()

    root1.mainloop()

# ========================================================
#           WINDOW: TICKET VIEW
# ========================================================
def show_ticket_window(passport_no):
    root4 = Tk()
    root4.title("YOUR TICKET")
    root4.geometry('500x500')
    root4['background'] = NEW_BG_COLOR

    try:
        # Get the most recent ticket for this passport number (using ORDER BY Ticket_id DESC)
        cursor.execute("SELECT TOP 1 Ticket_id, F_Name, L_Name, Source, Destination, Class, [Day] FROM Ticket WHERE PassportNo=? ORDER BY Ticket_id DESC", (passport_no,))
        data = cursor.fetchone()

        if data:
            Label(root4, text="FLIGHT TICKET", font=(BASE_FONT_FAMILY, 24, 'bold', 'underline'), bg=NEW_BG_COLOR, fg='yellow').pack(pady=20)
            
            info = f"""
            ================================
            Ticket ID   : {data[0]}
            Passenger   : {data[1]} {data[2]}
            Route       : {data[3]} 
                          to {data[4]}
            Class       : {data[5]}
            Travel Day  : {data[6]}
            Status      : PAID (Confirmed)
            ================================
            """
            Label(root4, text=info, font=('Courier', 12, 'bold'), justify=tk.LEFT, bg='white', relief='raised', padx=20, pady=20).pack(pady=10)
        else:
            Label(root4, text="Ticket not found!", font=(BASE_FONT_FAMILY, 18), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=50)

    except pyodbc.Error as e:
        messagebox.showerror("Error", str(e))

    Button(root4, text="Main Menu", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=lambda: go_back(root4)).pack(pady=20)
    root4.mainloop()

# ========================================================
#           WINDOW: PAYMENT GATEWAY
# ========================================================
def open_payment_window(flight_details, pass_data):
    pay_win = Tk()
    pay_win.title('PAYMENT GATEWAY')
    pay_win.geometry('450x550')
    pay_win['background'] = '#1A1A2E'

    Label(pay_win, text="Secure Checkout", font=(BASE_FONT_FAMILY, 22, 'bold'), fg='#E94560', bg='#1A1A2E').pack(pady=15)
    
    Label(pay_win, text=f"Total Amount to Pay: {flight_details['price']}", font=(BASE_FONT_FAMILY, 14, 'bold'), fg='#0F3460', bg='#FFFFFF', padx=10, pady=5).pack(pady=10)

    f = tk.Frame(pay_win, bg='#1A1A2E')
    f.pack(pady=10)

    Label(f, text="Payment Method:", font=(BASE_FONT_FAMILY, 11), fg='white', bg='#1A1A2E').grid(row=0, column=0, sticky='w', pady=10)
    method_box = ttk.Combobox(f, values=["bKash", "Nagad", "Credit/Debit Card"], state='readonly', width=22)
    method_box.current(0)
    method_box.grid(row=0, column=1, pady=10)

    Label(f, text="Account / Card No:", font=(BASE_FONT_FAMILY, 11), fg='white', bg='#1A1A2E').grid(row=1, column=0, sticky='w', pady=10)
    acc_ent = Entry(f, width=25)
    acc_ent.grid(row=1, column=1, pady=10)

    Label(f, text="PIN / CVV:", font=(BASE_FONT_FAMILY, 11), fg='white', bg='#1A1A2E').grid(row=2, column=0, sticky='w', pady=10)
    pin_ent = Entry(f, width=25, show='*')
    pin_ent.grid(row=2, column=1, pady=10)

    Label(f, text="Billing Address:", font=(BASE_FONT_FAMILY, 11), fg='white', bg='#1A1A2E').grid(row=3, column=0, sticky='w', pady=10)
    bill_ent = Entry(f, width=25)
    bill_ent.insert(0, pass_data["Address"]) 
    bill_ent.grid(row=3, column=1, pady=10)

    def process_payment():
        if not acc_ent.get() or not pin_ent.get() or not bill_ent.get():
            messagebox.showerror("Payment Error", "Please fill all payment details.", parent=pay_win)
            return
            
        messagebox.showinfo("Processing", f"Processing {flight_details['price']} via {method_box.get()}...", parent=pay_win)

        try:
            # 1. চেক করুন এই পাসপোর্ট নম্বরের যাত্রী আগে থেকেই ডেটাবেসে আছে কিনা
            cursor.execute("SELECT PassportNo FROM Passenger WHERE PassportNo=?", (pass_data["Passport No"],))
            existing_passenger = cursor.fetchone()

            # 2. যদি আগে থেকে ডেটাবেসে না থাকে, তবেই নতুন করে Passenger টেবিলে ইনসার্ট হবে
            if not existing_passenger:
                cursor.execute("INSERT INTO Passenger (PassportNo, F_Name, L_Name, Email, MobileNo, Address, DOB, Gender, Source, Destination, Class, [Day]) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                               (pass_data["Passport No"], pass_data["First Name"], pass_data["Last Name"], pass_data["Email"], pass_data["Mobile"], pass_data["Address"], pass_data["Date of Birth (YYYY-MM-DD)"], pass_data["Gender"], flight_details['source'], flight_details['dest'], pass_data["Class"], flight_details['day']))
            
            # 3. টিকিট টেবিলে সবসময় ইনসার্ট হবে (কারণ একজন মানুষ একাধিক টিকিট কাটতেই পারে)
            cursor.execute("INSERT INTO Ticket (PassportNo, Source, Destination, Class, [Day], F_Name, L_Name, MobileNo) VALUES (?,?,?,?,?,?,?,?)",
                           (pass_data["Passport No"], flight_details['source'], flight_details['dest'], pass_data["Class"], flight_details['day'], pass_data["First Name"], pass_data["Last Name"], pass_data["Mobile"]))
            
            connection.commit()
            
            trx_id = f"TRX{random.randint(100000, 999999)}"
            messagebox.showinfo("Payment Successful", f"Payment successful!\nTransaction ID: {trx_id}", parent=pay_win)
            
            pay_win.destroy()
            show_ticket_window(pass_data["Passport No"])

        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=pay_win)

    Button(pay_win, text="Pay & Confirm Ticket", font=(BASE_FONT_FAMILY, 12, 'bold'), bg='#E94560', fg='white', width=25, command=process_payment).pack(pady=20)
    Button(pay_win, text="Cancel", font=(BASE_FONT_FAMILY, 10), width=15, command=lambda: [pay_win.destroy(), create_main_menu()]).pack()

    pay_win.mainloop()

# ========================================================
#           WINDOW: BOOKING FORM
# ========================================================
def booking_window(flight_details):
    root3 = Tk()
    root3.title('FLIGHT BOOKING')
    root3.geometry('550x700')
    root3['background'] = NEW_BG_COLOR
    
    Label(root3, text="Passenger Details", font=(BASE_FONT_FAMILY, 22, 'bold'), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).pack(pady=10)
    Label(root3, text=f"{flight_details['name']} | {flight_details['date']}", font=(BASE_FONT_FAMILY, 10), fg='yellow', bg=NEW_BG_COLOR).pack()

    canvas = tk.Canvas(root3, bg=NEW_BG_COLOR, highlightthickness=0)
    frame = tk.Frame(canvas, bg=NEW_BG_COLOR)
    scroll = ttk.Scrollbar(root3, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)

    scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=frame, anchor="nw")
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    entries = {}
    fields = ["First Name", "Last Name", "Email", "Mobile", "Passport No", "Address", "Date of Birth (YYYY-MM-DD)"]

    r = 0
    for field in fields:
        Label(frame, text=field, font=(BASE_FONT_FAMILY, 11), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=r, column=0, sticky='w', padx=20, pady=5)
        
        if "Date of Birth" in field:
            ent = DateEntry(frame, width=27, date_pattern='y-mm-dd', background='darkblue', foreground='white', year=2026, maxdate=date.today())
        else:
            ent = Entry(frame, width=30)
            
        ent.grid(row=r+1, column=0, padx=20)
        entries[field] = ent
        r += 2

    Label(frame, text="Class", font=(BASE_FONT_FAMILY, 11), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=r, column=0, sticky='w', padx=20, pady=5)
    cls_box = ttk.Combobox(frame, values=get_classes(), state='readonly', width=27)
    cls_box.grid(row=r+1, column=0, padx=20)
    r += 2

    Label(frame, text="Gender", font=(BASE_FONT_FAMILY, 11), fg=NEW_FG_COLOR, bg=NEW_BG_COLOR).grid(row=r, column=0, sticky='w', padx=20, pady=5)
    gen_box = ttk.Combobox(frame, values=["Male", "Female", "Other"], state='readonly', width=27)
    gen_box.grid(row=r+1, column=0, padx=20)
    r += 2

    def proceed_to_pay():
        data = {k: v.get() for k, v in entries.items()}
        data["Class"] = cls_box.get()
        data["Gender"] = gen_box.get()

        if not all([data[k] for k in fields]) or not data["Class"] or not data["Gender"]:
            messagebox.showerror("Error", "All fields required.", parent=root3)
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", data["Email"]):
            messagebox.showerror("Error", "Invalid Email", parent=root3)
            return
        if not re.match(r"^01[3-9]\d{8}$", data["Mobile"]):
            messagebox.showerror("Error", "Invalid BD Mobile", parent=root3)
            return

        root3.destroy()
        open_payment_window(flight_details, data)

    tk.Button(frame, text="Proceed to Payment", font=(BASE_FONT_FAMILY, 11, 'bold'), width=20, bg='yellow', command=proceed_to_pay).grid(row=r+2, column=0, pady=20)
    tk.Button(frame, text="Cancel", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=lambda: go_back(root3)).grid(row=r+3, column=0, pady=5)

    root3.mainloop()

# ========================================================
#           WINDOW: CANCELLATION
# ========================================================
def cancellation_window():
    root5 = Tk()
    root5.title("CANCEL TICKET")
    root5.geometry('400x350')
    root5['background'] = NEW_BG_COLOR

    Label(root5, text="Cancel Reservation", font=(BASE_FONT_FAMILY, 20, 'bold'), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=20)

    Label(root5, text="Passport No:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=5)
    pass_ent = Entry(root5, width=25)
    pass_ent.pack()

    Label(root5, text="Ticket ID:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=5)
    ticket_ent = Entry(root5, width=25)
    ticket_ent.pack()

    def cancel_action():
        p = pass_ent.get()
        t = ticket_ent.get()
        
        if not p or not t:
            messagebox.showerror("Error", "All fields required.", parent=root5)
            return

        try:
            cursor.execute("SELECT * FROM Ticket WHERE PassportNo=? AND Ticket_id=?", (p, t))
            if not cursor.fetchone():
                messagebox.showerror("Error", "Ticket not found.", parent=root5)
                return

            if messagebox.askyesno("Confirm", "Are you sure you want to cancel this ticket?", parent=root5):
                cursor.execute("DELETE FROM Ticket WHERE Ticket_id=?", (t,))
                # টিকিট ডিলিট করার পর চেক করবে ওই ইউজারের আর কোনো টিকিট আছে কিনা
                cursor.execute("SELECT COUNT(*) FROM Ticket WHERE PassportNo=?", (p,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM Passenger WHERE PassportNo=?", (p,))
                
                connection.commit()
                messagebox.showinfo("Success", "Reservation Cancelled. Amount will be refunded to your payment method.", parent=root5)
                go_back(root5)

        except pyodbc.Error as e:
            messagebox.showerror("Database Error", str(e), parent=root5)

    Button(root5, text="Cancel Ticket", bg='red', fg='white', font=(BASE_FONT_FAMILY, 11, 'bold'), command=cancel_action).pack(pady=20)
    Button(root5, text="Back", font=(BASE_FONT_FAMILY, 11, 'bold'), command=lambda: go_back(root5)).pack()
    
    root5.mainloop()

# ========================================================
#           WINDOW: REGISTRATION
# ========================================================
def create_registration_window():
    reg_win = Tk()
    reg_win.title("REGISTER")
    reg_win.geometry('400x350')
    reg_win['background'] = NEW_BG_COLOR

    Label(reg_win, text="Create Account", font=(BASE_FONT_FAMILY, 20, 'bold'), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=20)

    Label(reg_win, text="Username:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack()
    u_ent = Entry(reg_win, width=25)
    u_ent.pack(pady=5)

    Label(reg_win, text="Password:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack()
    p_ent = Entry(reg_win, width=25, show='*')
    p_ent.pack(pady=5)

    def register():
        u = u_ent.get()
        p = p_ent.get()
        if u and p:
            try:
                cursor.execute("INSERT INTO Users VALUES (?,?)", (u, p))
                connection.commit()
                messagebox.showinfo("Success", "Registered Successfully! Login now.", parent=reg_win)
                go_to_login(reg_win)
            except pyodbc.Error:
                messagebox.showerror("Error", "Username already exists.", parent=reg_win)
        else:
            messagebox.showerror("Error", "Fields cannot be empty", parent=reg_win)

    Button(reg_win, text="Register", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=register).pack(pady=10)
    Button(reg_win, text="Back to Login", font=(BASE_FONT_FAMILY, 11), width=15, command=lambda: go_to_login(reg_win)).pack()

    reg_win.mainloop()

# ========================================================
#           WINDOW: LOGIN (ENTRY POINT)
# ========================================================
def create_login_window():
    login_win = Tk()
    login_win.title("LOGIN")
    login_win.geometry('450x350')
    login_win['background'] = NEW_BG_COLOR

    Label(login_win, text="USER LOGIN", font=(BASE_FONT_FAMILY, 24, 'bold'), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=30)

    Label(login_win, text="Username:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack()
    user_entry = Entry(login_win, width=30, font=(BASE_FONT_FAMILY, 10))
    user_entry.pack(pady=5)

    Label(login_win, text="Password:", font=(BASE_FONT_FAMILY, 12), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack()
    pass_entry = Entry(login_win, width=30, show='*', font=(BASE_FONT_FAMILY, 10))
    pass_entry.pack(pady=5)

    def login():
        u = user_entry.get()
        p = pass_entry.get()
        
        try:
            cursor.execute("SELECT * FROM Users WHERE Username=? AND Password=?", (u, p))
            if cursor.fetchone():
                login_win.destroy()
                create_main_menu()
            else:
                messagebox.showerror("Error", "Invalid Username or Password", parent=login_win)
        except pyodbc.Error as ex:
            messagebox.showerror("Database Error", str(ex), parent=login_win)

    def open_reg():
        login_win.destroy()
        create_registration_window()

    Button(login_win, text="Login", font=(BASE_FONT_FAMILY, 11, 'bold'), width=15, command=login).pack(pady=10)
    Button(login_win, text="Register Account", font=(BASE_FONT_FAMILY, 11), width=18, command=open_reg).pack()

    login_win.mainloop()

# ========================================================
#           WINDOW: MAIN MENU
# ========================================================
def create_main_menu():
    root = Tk()
    root.title("HOME")
    root.geometry('500x450')
    root['background'] = NEW_BG_COLOR

    Label(root, text="Flight Reservation System", font=(BASE_FONT_FAMILY, 24, 'bold'), bg=NEW_BG_COLOR, fg='yellow').pack(pady=40)
    Label(root, text="Welcome to Airline Reservation", font=(BASE_FONT_FAMILY, 14, 'italic'), bg=NEW_BG_COLOR, fg=NEW_FG_COLOR).pack(pady=10)

    btn_style = {'font': (BASE_FONT_FAMILY, 12, 'bold'), 'width': 20, 'height': 2}
    
    Button(root, text="Search & Book Flight", **btn_style, command=lambda: [root.destroy(), search_window()]).pack(pady=10)
    Button(root, text="Cancel Booking", **btn_style, command=lambda: [root.destroy(), cancellation_window()]).pack(pady=10)
    Button(root, text="Exit", **btn_style, bg='red', fg='white', command=root.destroy).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_login_window()