import os
import sys
import threading
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, font, ttk, Menu
import subprocess

BG_COLOR = "#000000"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#00d1ff"
SECONDARY_BG = "#121212"
BTN_START = "#00d1ff"
BTN_STOP = "#ff4b2b"
ENTRY_BG = "#1a1a1a"

class ShutdownManager:
    @staticmethod
    def shutdown(delay_seconds=1, restart=False):
        flag = "/r" if restart else "/s"
        try:
            subprocess.run(["shutdown", flag, "/t", str(delay_seconds)], check=True)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Action failed: {str(e)}")
            return False

    @staticmethod
    def cancel_shutdown():
        try:
            subprocess.run(["shutdown", "/a"], check=True)
            return True
        except Exception:
            return False

class TimeValidator:
    @staticmethod
    def parse_time(time_str):
        try:
            time_str = time_str.strip().upper()
            is_pm = "PM" in time_str
            is_am = "AM" in time_str
            clean_time = time_str.replace("AM", "").replace("PM", "").strip()
            
            if '.' in clean_time:
                parts = clean_time.split('.')
            elif ':' in clean_time:
                parts = clean_time.split(':')
            else:
                return None
            
            if len(parts) != 2:
                return None
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
                
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return None
            
            return hour, minute
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def parse_duration(duration_str):
        try:
            minutes = int(duration_str.strip())
            if minutes < 0:
                return None
            return minutes
        except (ValueError, AttributeError):
            return None

class ShutdownApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.update_loop()
    
    def setup_window(self):
        self.root.title("PC Shutdown Manager")
        self.root.geometry("500x380")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_variables(self):
        self.running = False
        self.thread = None
        self.shutdown_time = None
        self.shutdown_type = "shutdown"
        self.countdown_seconds = 0
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", background=SECONDARY_BG, foreground=FG_COLOR, padding=[15, 5], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", ACCENT_COLOR)], foreground=[("selected", "black")])
        style.configure("TFrame", background=BG_COLOR)
    
    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        time_frame = tk.Frame(notebook, bg=BG_COLOR)
        notebook.add(time_frame, text="Time Based")
        self.create_time_tab(time_frame)
        
        duration_frame = tk.Frame(notebook, bg=BG_COLOR)
        notebook.add(duration_frame, text="Duration Based")
        self.create_duration_tab(duration_frame)
        
        self.status_frame = tk.Frame(self.root, bg=SECONDARY_BG, relief=tk.FLAT, bd=0)
        self.status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="PC READY",
            font=("Segoe UI", 10, "bold"),
            bg=SECONDARY_BG,
            fg="#888888"
        )
        self.status_label.pack(pady=(10, 0))
        
        self.countdown_label = tk.Label(
            self.status_frame,
            text="00:00:00",
            font=("Segoe UI", 24, "bold"),
            bg=SECONDARY_BG,
            fg=ACCENT_COLOR
        )
        self.countdown_label.pack(pady=(0, 10))
    
    def create_time_tab(self, parent):
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        tk.Label(
            frame, 
            text="Shutdown Time:", 
            font=("Segoe UI", 12),
            bg=BG_COLOR, 
            fg=FG_COLOR
        ).pack(pady=5)
        
        self.time_entry = tk.Entry(
            frame, 
            width=15, 
            font=("Segoe UI", 14),
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            justify='center'
        )
        self.time_entry.pack(pady=5)
        self.time_entry.insert(0, datetime.now().strftime("%H.%M"))
        
        type_frame = tk.Frame(frame, bg=BG_COLOR)
        type_frame.pack(pady=10)
        
        self.action_type = tk.StringVar(value="shutdown")
        tk.Radiobutton(
            type_frame,
            text="Shutdown",
            variable=self.action_type,
            value="shutdown",
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="Restart",
            variable=self.action_type,
            value="restart",
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        btn_frame = tk.Frame(frame, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        
        self.toggle_btn = tk.Button(
            btn_frame,
            text="START SYSTEM",
            font=("Segoe UI", 10, "bold"),
            bg=BTN_START,
            fg="black",
            activebackground=ACCENT_COLOR,
            relief=tk.FLAT,
            width=18,
            height=2,
            command=self.toggle_time_based
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="CANCEL",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg="white",
            activebackground="#444444",
            relief=tk.FLAT,
            width=10,
            command=self.cancel_shutdown
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def create_duration_tab(self, parent):
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        tk.Label(
            frame,
            text="Minutes After:",
            font=("Segoe UI", 12),
            bg=BG_COLOR,
            fg=FG_COLOR
        ).pack(pady=5)
        
        self.duration_entry = tk.Entry(
            frame,
            width=15,
            font=("Segoe UI", 14),
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            justify='center'
        )
        self.duration_entry.pack(pady=5)
        self.duration_entry.insert(0, "60")
        
        type_frame = tk.Frame(frame, bg=BG_COLOR)
        type_frame.pack(pady=10)
        
        self.duration_action_type = tk.StringVar(value="shutdown")
        tk.Radiobutton(
            type_frame,
            text="Shutdown",
            variable=self.duration_action_type,
            value="shutdown",
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="Restart",
            variable=self.duration_action_type,
            value="restart",
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        btn_frame = tk.Frame(frame, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        
        self.duration_toggle_btn = tk.Button(
            btn_frame,
            text="START SYSTEM",
            font=("Segoe UI", 10, "bold"),
            bg=BTN_START,
            fg="black",
            activebackground=ACCENT_COLOR,
            relief=tk.FLAT,
            width=18,
            height=2,
            command=self.toggle_duration_based
        )
        self.duration_toggle_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn2 = tk.Button(
            btn_frame,
            text="CANCEL",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg="white",
            activebackground="#444444",
            relief=tk.FLAT,
            width=10,
            command=self.cancel_shutdown
        )
        cancel_btn2.pack(side=tk.LEFT, padx=5)
    
    def toggle_time_based(self):
        if not self.running:
            time_str = self.time_entry.get()
            parsed_time = TimeValidator.parse_time(time_str)
            
            if parsed_time is None:
                messagebox.showerror("Error", "Please enter a valid time!\nFormat: HH:MM or HH:MM AM/PM")
                return
            
            hour, minute = parsed_time
            now = datetime.now()
            shutdown_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if shutdown_time <= now:
                shutdown_time += timedelta(days=1)
            
            self.shutdown_time = shutdown_time
            self.shutdown_type = self.action_type.get()
            self.start_monitoring()
            
            self.toggle_btn.config(text="STOP", bg=BTN_STOP, fg="white")
        else:
            self.stop_monitoring()
            self.toggle_btn.config(text="START SYSTEM", bg=BTN_START, fg="black")
    
    def toggle_duration_based(self):
        if not self.running:
            duration_str = self.duration_entry.get()
            minutes = TimeValidator.parse_duration(duration_str)
            
            if minutes is None:
                messagebox.showerror("Error", "Please enter a valid duration in minutes!")
                return
            
            self.shutdown_time = datetime.now() + timedelta(minutes=minutes)
            self.shutdown_type = self.duration_action_type.get()
            self.start_monitoring()
            
            self.duration_toggle_btn.config(text="STOP", bg=BTN_STOP, fg="white")
        else:
            self.stop_monitoring()
            self.duration_toggle_btn.config(text="START SYSTEM", bg=BTN_START, fg="black")
    
    def start_monitoring(self):
        self.running = True
        self.thread = threading.Thread(target=self.monitor_shutdown, daemon=True)
        self.thread.start()
        self.update_status_display()
    
    def stop_monitoring(self):
        self.running = False
        self.shutdown_time = None
        self.update_status_display()
        ShutdownManager.cancel_shutdown()
    
    def monitor_shutdown(self):
        while self.running:
            if self.shutdown_time is None:
                break
            if datetime.now() >= self.shutdown_time:
                self.execute_shutdown()
                break
            time.sleep(1)
    
    def execute_shutdown(self):
        self.running = False
        is_restart = self.shutdown_type == "restart"
        action_name = "restart" if is_restart else "shutdown"
        
        messagebox.showinfo("Status", f"Time is up!\nPC will {action_name} now...")
        ShutdownManager.shutdown(delay_seconds=1, restart=is_restart)
        self.reset_ui()

    def update_status_display(self):
        if self.running and self.shutdown_time:
            now = datetime.now()
            time_diff = self.shutdown_time - now
            
            if time_diff.total_seconds() > 0:
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.status_label.config(text=f"SYSTEM ACTIVE - TARGET: {self.shutdown_time.strftime('%H:%M:%S')}", fg=ACCENT_COLOR)
                self.countdown_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.status_label.config(text="EXECUTING...", fg=BTN_STOP)
                self.countdown_label.config(text="00:00:00")
        else:
            self.status_label.config(text="PC READY", fg="#666666")
            self.countdown_label.config(text="00:00:00")

    def update_loop(self):
        self.update_status_display()
        self.root.after(1000, self.update_loop)

    def cancel_shutdown(self):
        if ShutdownManager.cancel_shutdown():
            self.stop_monitoring()
            self.reset_ui()
            messagebox.showinfo("Success", "Action canceled.")
        else:
            messagebox.showinfo("Info", "No active action to cancel.")

    def reset_ui(self):
        for btn in [self.toggle_btn, self.duration_toggle_btn]:
            btn.config(text="START SYSTEM", bg=BTN_START, fg="black")

def main():
    root = tk.Tk()
    app = ShutdownApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
