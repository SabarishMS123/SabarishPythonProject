"""
Main Tkinter application – modern glassmorphism-inspired AI Assistant Hub.
Handles navigation between Login → Register → Dashboard → Chatbot screens.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
import math
import random
import time

from ui.styles import COLORS, FONTS
from services.database import db
from services.email_service import generate_verification_code, send_verification_email
from services.groq_service import groq_service, AI_DISPLAY_NAMES, AI_COLORS, AI_ICONS, SYSTEM_PROMPTS


class NightSkyFrame(tk.Frame):
    """A frame with its own visible night-sky canvas behind its child widgets."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "#040b1a")
        super().__init__(parent, **kwargs)
        self.sky_canvas = tk.Canvas(self, bg="#040b1a", highlightthickness=0, bd=0)
        self.sky_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Canvas.lower() is for canvas *items*; use Tk's widget-level command.
        self.tk.call("lower", self.sky_canvas._w)
        self._sky_size = None
        self.bind("<Configure>", self._redraw_night_sky)

    def _redraw_night_sky(self, event=None):
        width, height = max(self.winfo_width(), 1), max(self.winfo_height(), 1)
        if self._sky_size == (width, height):
            return
        self._sky_size = (width, height)
        canvas = self.sky_canvas
        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, height, fill="#040b1a", outline="")

        for gx, gy, radius, color in [
            (width * .20, height * .32, 220, "#1d2f5d"),
            (width * .72, height * .64, 260, "#1b2548"),
            (width * .50, height * .16, 180, "#232b57"),
        ]:
            canvas.create_oval(gx-radius, gy-radius, gx+radius, gy+radius,
                               fill=color, outline="", stipple="gray50")

        random.seed(42)
        for _ in range(220):
            x, y = random.randint(0, width), random.randint(0, int(height * .9))
            size, brightness = random.uniform(.8, 2.4), random.randint(140, 255)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline="")

        moon_x, moon_y = int(width * .82), int(height * .22)
        moon_radius = max(44, int(min(width, height) * .08))
        canvas.create_oval(moon_x-moon_radius-18, moon_y-moon_radius-18,
                           moon_x+moon_radius+18, moon_y+moon_radius+18,
                           fill="#f3d77d", outline="", stipple="gray25")
        canvas.create_oval(moon_x-moon_radius, moon_y-moon_radius,
                           moon_x+moon_radius, moon_y+moon_radius,
                           fill="#f8e9a1", outline="#d9b84d", width=2)
        for dx, dy, radius in [(-18, -12, 8), (15, -10, 6), (-10, 20, 7), (22, 13, 5)]:
            canvas.create_oval(moon_x+dx-radius, moon_y+dy-radius,
                               moon_x+dx+radius, moon_y+dy+radius,
                               fill="#d9c780", outline="")


class AIAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Assistant Hub")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg="#000000")
        self.current_user = None
        self.current_ai = None
        self.current_session_id = None

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.winfo_screenheight() // 2) - (720 // 2)
        self.geometry(f"+{x}+{y}")

        # Each screen owns its sky canvas because Tkinter frames are opaque.
        self.container = tk.Frame(self, bg="#040b1a", highlightthickness=0)
        self.container.place(x=0, y=0, relwidth=1, relheight=1)

        self.frames = {}
        self._build_frames()
        self.show_frame("Login")

    def _build_frames(self):
        for name, FrameClass in [
            ("Login", LoginFrame),
            ("Register", RegisterFrame),
            ("Dashboard", DashboardFrame),
            ("Chatbot", ChatbotFrame),
        ]:
            frame = FrameClass(self.container, self)
            self.frames[name] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def login_success(self, user: dict):
        self.current_user = user
        self.show_frame("Dashboard")

    def logout(self):
        self.current_user = None
        self.current_ai = None
        self.current_session_id = None
        self.show_frame("Login")

    def _draw_night_sky(self):
        """Draw a full-window night sky with stars, moon glow, and subtle nebula haze."""
        self.background_canvas.delete("all")

        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)

        # Deep space base and gentle nebula glow
        self.background_canvas.create_rectangle(
            0, 0, width, height,
            fill="#040b1a", outline=""
        )
        for glow in [
            (width * 0.22, height * 0.35, 220, "#1d2f5d"),
            (width * 0.72, height * 0.62, 260, "#1b2548"),
            (width * 0.52, height * 0.18, 180, "#232b57"),
        ]:
            gx, gy, radius, color = glow
            self.background_canvas.create_oval(
                gx - radius, gy - radius, gx + radius, gy + radius,
                fill=color, outline="", stipple="gray50"
            )

        # Big star field
        random.seed(42)
        for _ in range(220):
            x = random.randint(0, width)
            y = random.randint(0, int(height * 0.9))
            size = random.uniform(0.8, 2.4)
            brightness = random.randint(140, 255)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            self.background_canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=""
            )

        # Add a few larger sparkling stars
        for _ in range(25):
            x = random.randint(0, width)
            y = random.randint(0, int(height * 0.8))
            self.background_canvas.create_line(
                x - 5, y, x + 5, y, fill="#dbeafe", width=1
            )
            self.background_canvas.create_line(
                x, y - 5, x, y + 5, fill="#dbeafe", width=1
            )

        # Draw moon with glow
        moon_x, moon_y = int(width * 0.82), int(height * 0.22)
        moon_radius = max(44, int(min(width, height) * 0.08))
        self.background_canvas.create_oval(
            moon_x - moon_radius - 18, moon_y - moon_radius - 18,
            moon_x + moon_radius + 18, moon_y + moon_radius + 18,
            fill="#f3d77d", outline="", stipple="gray25"
        )
        self.background_canvas.create_oval(
            moon_x - moon_radius, moon_y - moon_radius,
            moon_x + moon_radius, moon_y + moon_radius,
            fill="#f8e9a1", outline="#d9b84d", width=2
        )

        # Add lunar craters
        crater_positions = [
            (moon_x - 18, moon_y - 12, 8),
            (moon_x + 15, moon_y - 10, 6),
            (moon_x - 10, moon_y + 20, 7),
            (moon_x + 22, moon_y + 13, 5),
        ]
        for cx, cy, cr in crater_positions:
            self.background_canvas.create_oval(
                cx - cr, cy - cr, cx + cr, cy + cr,
                fill="#d9c780", outline=""
            )

        # Store moon position for satellite orbit
        self.moon_pos = (moon_x, moon_y)
        self.moon_radius = moon_radius

    def animate_background(self):
        """Animate satellites orbiting the moon"""
        try:
            if hasattr(self, "moon_pos"):
                moon_x, moon_y = self.moon_pos
                orbit_radius = 120
                
                # Draw 3 orbiting satellites
                for i in range(3):
                    angle = (self.satellite_angle + i * 120) * math.pi / 180
                    sat_x = moon_x + orbit_radius * math.cos(angle)
                    sat_y = moon_y + orbit_radius * math.sin(angle)
                    
                    # Draw satellite as small glowing dot
                    self.background_canvas.create_oval(
                        sat_x - 3, sat_y - 3, sat_x + 3, sat_y + 3,
                        fill="#00ff88", outline="#00cc66"
                    )
                    
                    # Draw orbit line
                    if i == 0:
                        self.background_canvas.create_oval(
                            moon_x - orbit_radius, moon_y - orbit_radius,
                            moon_x + orbit_radius, moon_y + orbit_radius,
                            outline="#1a3a4a", width=1
                        )
                
                # Update angle for next frame
                self.satellite_angle += 2
                if self.satellite_angle >= 360:
                    self.satellite_angle = 0
                
                # Schedule next animation frame
                self.after(50, self.animate_background)
        except tk.TclError:
            # Window closed
            pass


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN FRAME
# ─────────────────────────────────────────────────────────────────────────────

class LoginFrame(NightSkyFrame):
    def __init__(self, parent, controller: AIAssistantApp):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Center card
        card = tk.Frame(self, bg=COLORS["card"], highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=480)

        # Accent bar at top
        accent = tk.Frame(card, bg=COLORS["accent"], height=4)
        accent.pack(fill="x")

        content = tk.Frame(card, bg=COLORS["card"])
        content.pack(fill="both", expand=True, padx=40, pady=30)

        tk.Label(content, text="✨ AI Assistant Hub", font=FONTS["title"],
                 fg=COLORS["text"], bg=COLORS["card"]).pack(pady=(10, 4))
        tk.Label(content, text="Sign in to continue", font=FONTS["body"],
                 fg=COLORS["text_muted"], bg=COLORS["card"]).pack(pady=(0, 28))

        # Email
        tk.Label(content, text="Email", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.email_entry = self._styled_entry(content)
        self.email_entry.pack(fill="x", pady=(4, 16), ipady=8)

        # Password
        tk.Label(content, text="Password", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.password_entry = self._styled_entry(content, show="•")
        self.password_entry.pack(fill="x", pady=(4, 8), ipady=8)

        # Error label
        self.error_label = tk.Label(content, text="", font=FONTS["small"],
                                    fg=COLORS["danger"], bg=COLORS["card"])
        self.error_label.pack(pady=(4, 12))

        # Login button
        login_btn = tk.Button(
            content, text="Sign In", font=FONTS["button"],
            bg=COLORS["accent"], fg="#0b0b14", activebackground=COLORS["accent_hover"],
            activeforeground="#0b0b14", relief="flat", cursor="hand2",
            command=self._do_login
        )
        login_btn.pack(fill="x", ipady=10, pady=(4, 16))

        # Register link
        link_frame = tk.Frame(content, bg=COLORS["card"])
        link_frame.pack()
        tk.Label(link_frame, text="Don't have an account? ", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"]).pack(side="left")
        register_link = tk.Label(link_frame, text="Create one", font=FONTS["small"],
                                 fg=COLORS["accent"], bg=COLORS["card"], cursor="hand2")
        register_link.pack(side="left")
        register_link.bind("<Button-1>", lambda e: self.controller.show_frame("Register"))

        # Bind Enter key
        self.email_entry.bind("<Return>", lambda e: self._do_login())
        self.password_entry.bind("<Return>", lambda e: self._do_login())

    def _styled_entry(self, parent, show=None):
        entry = tk.Entry(
            parent, font=FONTS["body"], bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat",
            highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"]
        )
        if show:
            entry.configure(show=show)
        return entry

    def _do_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        self.error_label.config(text="")

        if not email or not password:
            self.error_label.config(text="Please fill in all fields.")
            return

        user = db.authenticate(email, password)
        if user:
            self.email_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
            self.controller.login_success(user)
        else:
            self.error_label.config(text="Invalid credentials or email not verified.")

    def on_show(self):
        self.error_label.config(text="")
        self.email_entry.focus_set()


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER FRAME
# ─────────────────────────────────────────────────────────────────────────────

class RegisterFrame(NightSkyFrame):
    def __init__(self, parent, controller: AIAssistantApp):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self.pending_email = None
        self._build_ui()

    def _build_ui(self):
        card = tk.Frame(self, bg=COLORS["card"], highlightbackground=COLORS["border"],
                        highlightthickness=1)
        self.card = card  # Store reference for dynamic resizing
        card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=580)
        self.card_height = 580  # Track initial height

        accent = tk.Frame(card, bg=COLORS["accent"], height=4)
        accent.pack(fill="x")

        content = tk.Frame(card, bg=COLORS["card"])
        content.pack(fill="both", expand=True, padx=36, pady=24)

        tk.Label(content, text="Create Account", font=FONTS["heading"],
                 fg=COLORS["text"], bg=COLORS["card"]).pack(pady=(4, 2))
        tk.Label(content, text="We'll send a verification code to your email",
                 font=FONTS["small"], fg=COLORS["text_muted"], bg=COLORS["card"]).pack(pady=(0, 18))

        # Full name
        tk.Label(content, text="Full Name", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.name_entry = self._styled_entry(content)
        self.name_entry.pack(fill="x", pady=(3, 12), ipady=7)

        # Email
        tk.Label(content, text="Email", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.email_entry = self._styled_entry(content)
        self.email_entry.pack(fill="x", pady=(3, 12), ipady=7)

        # Password
        tk.Label(content, text="Password", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.password_entry = self._styled_entry(content, show="•")
        self.password_entry.pack(fill="x", pady=(3, 12), ipady=7)

        # Confirm password
        tk.Label(content, text="Confirm Password", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.confirm_entry = self._styled_entry(content, show="•")
        self.confirm_entry.pack(fill="x", pady=(3, 10), ipady=7)

        self.error_label = tk.Label(content, text="", font=FONTS["small"],
                                    fg=COLORS["danger"], bg=COLORS["card"])
        self.error_label.pack(pady=(0, 8))

        # Step 1 button
        self.register_btn = tk.Button(
            content, text="Send Verification Code", font=FONTS["button"],
            bg=COLORS["accent"], fg="#0b0b14", activebackground=COLORS["accent_hover"],
            relief="flat", cursor="hand2", command=self._send_code
        )
        self.register_btn.pack(fill="x", ipady=9, pady=(0, 12))

        # Verification section (initially hidden)
        self.verify_frame = tk.Frame(content, bg=COLORS["card"])
        # not packed yet

        tk.Label(self.verify_frame, text="Verification Code", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"], anchor="w").pack(fill="x")
        self.code_entry = self._styled_entry(self.verify_frame)
        self.code_entry.pack(fill="x", pady=(3, 10), ipady=7)

        self.verify_btn = tk.Button(
            self.verify_frame, text="Verify & Complete Registration", font=FONTS["button"],
            bg=COLORS["success"], fg="#0b0b14", activebackground="#6ee7b7",
            relief="flat", cursor="hand2", command=self._verify_code
        )
        self.verify_btn.pack(fill="x", ipady=9)

        # Back to login (stored for later reordering)
        self.link_frame = tk.Frame(content, bg=COLORS["card"])
        self.link_frame.pack(pady=(16, 0))
        tk.Label(self.link_frame, text="Already have an account? ", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=COLORS["card"]).pack(side="left")
        login_link = tk.Label(self.link_frame, text="Sign in", font=FONTS["small"],
                              fg=COLORS["accent"], bg=COLORS["card"], cursor="hand2")
        login_link.pack(side="left")
        login_link.bind("<Button-1>", lambda e: self.controller.show_frame("Login"))

    def _styled_entry(self, parent, show=None):
        entry = tk.Entry(
            parent, font=FONTS["body"], bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat",
            highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"]
        )
        if show:
            entry.configure(show=show)
        return entry

    def _send_code(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        self.error_label.config(text="")

        if not name or not email or not password:
            self.error_label.config(text="All fields are required.")
            return
        if password != confirm:
            self.error_label.config(text="Passwords do not match.")
            return
        if len(password) < 6:
            self.error_label.config(text="Password must be at least 6 characters.")
            return
        if "@" not in email or "." not in email:
            self.error_label.config(text="Please enter a valid email.")
            return

        code = generate_verification_code()
        user_id = db.create_user(email, password, name, code)
        if user_id is None:
            self.error_label.config(text="Email already registered.")
            return

        # Send email (async-ish)
        send_verification_email(email, code, name)
        self.pending_email = email

        # Show verification UI - unpack link_frame, then pack verify_frame, then repack link_frame
        self.error_label.config(text="Check your email (or console) for the code.", fg=COLORS["success"])
        self.register_btn.config(state="disabled", text="Code Sent ✓")

        # Expand card to fit verification section
        self.card_height = 680
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=self.card_height)

        self.link_frame.pack_forget()  # Temporarily remove link frame
        self.verify_frame.pack(fill="x", pady=(12, 0))  # Pack verification frame
        self.link_frame.pack(pady=(16, 0))  # Repack link frame at the bottom

        self.code_entry.focus_set()
        self.update_idletasks()

    def _verify_code(self):
        code = self.code_entry.get().strip()
        if not code or not self.pending_email:
            self.error_label.config(text="Enter the verification code.", fg=COLORS["danger"])
            return

        if db.verify_user(self.pending_email, code):
            messagebox.showinfo("Success", "Account verified! You can now sign in.")
            self._reset()
            self.controller.show_frame("Login")
        else:
            self.error_label.config(text="Invalid or expired code.", fg=COLORS["danger"])

    def _reset(self):
        self.name_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.confirm_entry.delete(0, "end")
        self.code_entry.delete(0, "end")
        self.error_label.config(text="")
        self.register_btn.config(state="normal", text="Send Verification Code")
        
        # Hide verification frame and reorder widgets
        self.verify_frame.pack_forget()
        self.link_frame.pack_forget()
        self.link_frame.pack(pady=(16, 0))
        
        # Shrink card back to original height
        self.card_height = 580
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=self.card_height)
        
        self.pending_email = None

    def on_show(self):
        self._reset()
        self.name_entry.focus_set()


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD FRAME
# ─────────────────────────────────────────────────────────────────────────────

class DashboardFrame(NightSkyFrame):
    def __init__(self, parent, controller: AIAssistantApp):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=COLORS["bg_secondary"], height=64)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="✨ AI Assistant Hub", font=FONTS["heading"],
                 fg=COLORS["text"], bg=COLORS["bg_secondary"]).pack(side="left", padx=24, pady=16)

        self.user_label = tk.Label(top, text="", font=FONTS["body"],
                                   fg=COLORS["text_muted"], bg=COLORS["bg_secondary"])
        self.user_label.pack(side="left", padx=8)

        logout_btn = tk.Button(
            top, text="Logout", font=FONTS["small"], bg=COLORS["card"],
            fg=COLORS["text_muted"], activebackground=COLORS["card_hover"],
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self.controller.logout
        )
        logout_btn.pack(side="right", padx=24)

        # Welcome + grid
        body = NightSkyFrame(self)
        body.pack(fill="both", expand=True, padx=40, pady=30)

        tk.Label(body, text="Choose your AI Companion", font=FONTS["heading"],
                 fg=COLORS["text"], bg="#040b1a").pack(anchor="w", pady=(0, 6))
        tk.Label(body, text="Each specialist is fine-tuned for its domain. Your chats are saved automatically.",
                 font=FONTS["body"], fg=COLORS["text_muted"], bg="#040b1a").pack(anchor="w", pady=(0, 28))

        # Cards grid
        grid = NightSkyFrame(body)
        grid.pack(fill="both", expand=True)

        ais = [
            ("tax", "Tax AI", "Tax concepts, deductions, filing tips & planning"),
            ("professional", "Professional AI", "Career growth, interviews, leadership & soft skills"),
            ("coding", "Coding Assistant AI", "Code help, debugging, architecture & best practices"),
            ("food", "Food Assistant AI", "Recipes, meal plans, techniques & culinary ideas"),
            ("travel", "Travelling Plan AI", "Itineraries, destinations, packing & travel tips"),
        ]

        for i, (key, title, desc) in enumerate(ais):
            row, col = divmod(i, 3)
            card = self._create_ai_card(grid, key, title, desc)
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

        for c in range(3):
            grid.columnconfigure(c, weight=1)
        for r in range(2):
            grid.rowconfigure(r, weight=1)

    def _create_ai_card(self, parent, key, title, desc):
        color = AI_COLORS.get(key, COLORS["accent"])
        icon = AI_ICONS.get(key, "🤖")

        card = tk.Frame(parent, bg=COLORS["card"], highlightbackground=COLORS["border"],
                        highlightthickness=1, cursor="hand2")

        # Color accent strip
        strip = tk.Frame(card, bg=color, height=4)
        strip.pack(fill="x")

        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(inner, text=f"{icon}  {title}", font=FONTS["subheading"],
                 fg=COLORS["text"], bg=COLORS["card"], anchor="w").pack(fill="x")
        tk.Label(inner, text=desc, font=FONTS["small"], fg=COLORS["text_muted"],
                 bg=COLORS["card"], wraplength=220, justify="left", anchor="w").pack(fill="x", pady=(8, 16))

        open_btn = tk.Button(
            inner, text="Open →", font=FONTS["button"], bg=color, fg="#0b0b14",
            activebackground=COLORS["accent_hover"], relief="flat", cursor="hand2",
            command=lambda k=key: self._open_ai(k)
        )
        open_btn.pack(anchor="w", ipadx=12, ipady=4)

        # Hover effect
        def on_enter(e):
            card.configure(highlightbackground=color)
        def on_leave(e):
            card.configure(highlightbackground=COLORS["border"])
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        for child in card.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

        return card

    def _open_ai(self, ai_type: str):
        self.controller.current_ai = ai_type
        self.controller.current_session_id = None
        self.controller.show_frame("Chatbot")

    def on_show(self):
        user = self.controller.current_user
        if user:
            self.user_label.config(text=f"Hello, {user['full_name']}")


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT FRAME
# ─────────────────────────────────────────────────────────────────────────────

class ChatbotFrame(NightSkyFrame):
    def __init__(self, parent, controller: AIAssistantApp):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # ── Left sidebar (chat history) ──
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar header
        side_header = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        side_header.pack(fill="x", padx=12, pady=14)

        self.side_title = tk.Label(side_header, text="Chats", font=FONTS["subheading"],
                                   fg=COLORS["text"], bg=COLORS["sidebar"])
        self.side_title.pack(side="left")

        new_btn = tk.Button(
            side_header, text="+ New", font=FONTS["small"], bg=COLORS["accent"],
            fg="#0b0b14", relief="flat", cursor="hand2", padx=8, pady=2,
            command=self._new_chat
        )
        new_btn.pack(side="right")

        # Scrollable session list
        self.session_canvas = tk.Canvas(self.sidebar, bg=COLORS["sidebar"],
                                        highlightthickness=0)
        self.session_scroll = ttk.Scrollbar(self.sidebar, orient="vertical",
                                            command=self.session_canvas.yview)
        self.session_list = tk.Frame(self.session_canvas, bg=COLORS["sidebar"])

        self.session_list.bind(
            "<Configure>",
            lambda e: self.session_canvas.configure(scrollregion=self.session_canvas.bbox("all"))
        )
        self.session_canvas.create_window((0, 0), window=self.session_list, anchor="nw", width=240)
        self.session_canvas.configure(yscrollcommand=self.session_scroll.set)

        self.session_canvas.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.session_scroll.pack(side="right", fill="y")

        # ── Main chat area ──
        main = NightSkyFrame(self)
        main.pack(side="left", fill="both", expand=True)

        # Chat header
        self.chat_header = tk.Frame(main, bg=COLORS["bg_secondary"], height=56)
        self.chat_header.pack(fill="x")
        self.chat_header.pack_propagate(False)

        self.header_label = tk.Label(
            self.chat_header, text="", font=FONTS["subheading"],
            fg=COLORS["text"], bg=COLORS["bg_secondary"]
        )
        self.header_label.pack(side="left", padx=20, pady=14)

        # Back button in header (right side)
        back_btn = tk.Button(
            self.chat_header, text="← Back to AI Selection", font=FONTS["small"],
            bg=COLORS["accent"], fg="#0b0b14", activebackground=COLORS["accent_hover"],
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=lambda: self.controller.show_frame("Dashboard")
        )
        back_btn.pack(side="right", padx=20, pady=8)

        # Messages area with Canvas for bubble-style chat
        self.msg_frame = NightSkyFrame(main)
        self.msg_frame.pack(fill="both", expand=True)

        # Canvas with scrollbar for messages
        self.msg_canvas = tk.Canvas(
            self.msg_frame, bg=COLORS["bg"], highlightthickness=0
        )
        self.msg_scrollbar = ttk.Scrollbar(
            self.msg_frame, orient="vertical", command=self.msg_canvas.yview
        )
        self.msg_content = tk.Frame(self.msg_canvas, bg=COLORS["bg"])

        self.msg_content.bind(
            "<Configure>",
            lambda e: self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all"))
        )
        self.msg_canvas.create_window((0, 0), window=self.msg_content, anchor="nw", width=800)
        self.msg_canvas.configure(yscrollcommand=self.msg_scrollbar.set)

        self.msg_canvas.pack(side="left", fill="both", expand=True)
        self.msg_scrollbar.pack(side="right", fill="y")

        # Input area
        input_area = tk.Frame(main, bg=COLORS["bg_secondary"], height=90)
        input_area.pack(fill="x")
        input_area.pack_propagate(False)

        input_inner = tk.Frame(input_area, bg=COLORS["bg_secondary"])
        input_inner.pack(fill="both", expand=True, padx=20, pady=14)

        self.input_entry = tk.Text(
            input_inner, height=2, font=FONTS["body"], bg=COLORS["input_bg"],
            fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat",
            highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"], padx=12, pady=8, wrap="word"
        )
        self.input_entry.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.bind("<Shift-Return>", lambda e: None)  # allow newline

        self.send_btn = tk.Button(
            input_inner, text="Send", font=FONTS["button"], bg=COLORS["accent"],
            fg="#0b0b14", activebackground=COLORS["accent_hover"], relief="flat",
            cursor="hand2", padx=20, command=self._send_message
        )
        self.send_btn.pack(side="right", ipady=8)

    def on_show(self):
        ai = self.controller.current_ai
        if not ai:
            self.controller.show_frame("Dashboard")
            return

        name = AI_DISPLAY_NAMES.get(ai, ai)
        icon = AI_ICONS.get(ai, "🤖")
        color = AI_COLORS.get(ai, COLORS["accent"])
        self.header_label.config(text=f"{icon}  {name}")
        self.side_title.config(text=f"{icon} Chats")

        self._refresh_sessions()
        if self.controller.current_session_id is None:
            self._new_chat()
        else:
            self._load_session(self.controller.current_session_id)

    def _refresh_sessions(self):
        # Clear list
        for w in self.session_list.winfo_children():
            w.destroy()

        user_id = self.controller.current_user["id"]
        ai = self.controller.current_ai
        sessions = db.get_sessions(user_id, ai)

        if not sessions:
            tk.Label(self.session_list, text="No chats yet", font=FONTS["small"],
                     fg=COLORS["text_dim"], bg=COLORS["sidebar"]).pack(pady=20)
            return

        for s in sessions:
            self._add_session_item(s)

    def _add_session_item(self, session: dict):
        sid = session["id"]
        title = session["title"][:28] + ("…" if len(session["title"]) > 28 else "")
        pinned = session["is_pinned"]
        is_active = sid == self.controller.current_session_id

        bg = COLORS["card"] if is_active else COLORS["sidebar"]
        frame = tk.Frame(self.session_list, bg=bg, cursor="hand2")
        frame.pack(fill="x", pady=2, padx=4)

        pin_icon = "📌 " if pinned else ""
        lbl = tk.Label(frame, text=f"{pin_icon}{title}", font=FONTS["small"],
                       fg=COLORS["text"], bg=bg, anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        # Actions
        btn_frame = tk.Frame(frame, bg=bg)
        btn_frame.pack(side="right", padx=4)

        pin_btn = tk.Button(
            btn_frame, text="📌" if not pinned else "📍", font=("Segoe UI", 9),
            bg=bg, fg=COLORS["text_muted"], relief="flat", cursor="hand2",
            command=lambda s=sid, p=not pinned: self._toggle_pin(s, p)
        )
        pin_btn.pack(side="left")

        del_btn = tk.Button(
            btn_frame, text="🗑", font=("Segoe UI", 9),
            bg=bg, fg=COLORS["danger"], relief="flat", cursor="hand2",
            command=lambda s=sid: self._delete_session(s)
        )
        del_btn.pack(side="left")

        def select(e, s=sid):
            self._load_session(s)

        frame.bind("<Button-1>", select)
        lbl.bind("<Button-1>", select)

    def _new_chat(self):
        user_id = self.controller.current_user["id"]
        ai = self.controller.current_ai
        sid = db.create_session(user_id, ai, "New Chat")
        self.controller.current_session_id = sid
        self._clear_display()
        self._append_system(f"Started a new conversation with {AI_DISPLAY_NAMES.get(ai, ai)}.")
        self._refresh_sessions()
        self.input_entry.focus_set()

    def _load_session(self, session_id: int):
        self.controller.current_session_id = session_id
        self._clear_display()
        messages = db.get_messages(session_id)
        if not messages:
            ai = self.controller.current_ai
            self._append_system(f"Conversation with {AI_DISPLAY_NAMES.get(ai, ai)}. Ask anything!")
        else:
            for m in messages:
                self._append_message(m["role"], m["content"], m["created_at"])
        self._refresh_sessions()
        self.input_entry.focus_set()

    def _toggle_pin(self, session_id: int, pin: bool):
        db.pin_session(session_id, pin)
        self._refresh_sessions()

    def _delete_session(self, session_id: int):
        if messagebox.askyesno("Delete Chat", "Are you sure you want to delete this chat?"):
            db.delete_session(session_id)
            if self.controller.current_session_id == session_id:
                self.controller.current_session_id = None
                self._new_chat()
            else:
                self._refresh_sessions()

    def _clear_display(self):
        for widget in self.msg_content.winfo_children():
            widget.destroy()

    def _append_system(self, text: str):
        """Add a centered system message"""
        msg_frame = tk.Frame(self.msg_content, bg=COLORS["bg"])
        msg_frame.pack(fill="x", padx=20, pady=12)

        # Center the system message
        center_frame = tk.Frame(msg_frame, bg=COLORS["bg"])
        center_frame.pack(anchor="center")

        label = tk.Label(
            center_frame, text=text, font=FONTS["small"],
            fg=COLORS["text_muted"], bg=COLORS["bg"], wraplength=500, justify="center"
        )
        label.pack()

        self.msg_canvas.yview_moveto(1.0)

    def _append_message(self, role: str, content: str, timestamp=None):
        """Add a message bubble (user=right, assistant=left)"""
        is_user = role == "user"
        
        # Outer frame for padding
        msg_frame = tk.Frame(self.msg_content, bg=COLORS["bg"])
        msg_frame.pack(fill="x", padx=12, pady=8)

        # Determine colors and alignment
        if is_user:
            bubble_bg = COLORS["accent"]
            text_fg = "#0b0b14"
            anchor = "e"  # Right align
            padx = (250, 12)  # Push user messages to the right
        else:
            bubble_bg = COLORS["card"]
            text_fg = COLORS["text"]
            anchor = "w"  # Left align
            padx = (12, 80)

        # Bubble container
        bubble = tk.Frame(msg_frame, bg=bubble_bg, relief="flat")
        bubble.pack(anchor=anchor, padx=padx, fill="x", expand=False, ipadx=2)

        # Content inside bubble
        content_frame = tk.Frame(bubble, bg=bubble_bg)
        content_frame.pack(fill="x", padx=12, pady=10)

        # Sender name
        sender = "You" if is_user else AI_DISPLAY_NAMES.get(self.controller.current_ai, "AI")
        name_label = tk.Label(
            content_frame, text=sender, font=FONTS["body_bold"],
            fg=text_fg, bg=bubble_bg
        )
        name_label.pack(anchor="w")

        # Message content with word wrap
        content_label = tk.Label(
            content_frame, text=content, font=FONTS["body"],
            fg=text_fg, bg=bubble_bg, wraplength=350, justify="left"
        )
        content_label.pack(anchor="w", fill="x", pady=(4, 0))

        # Timestamp
        if timestamp:
            if isinstance(timestamp, datetime):
                time_str = timestamp.strftime("%H:%M")
            else:
                time_str = str(timestamp)[:16]
            time_label = tk.Label(
                content_frame, text=time_str, font=FONTS["small"],
                fg=text_fg if is_user else COLORS["text_dim"], bg=bubble_bg
            )
            time_label.pack(anchor="e", pady=(4, 0))

        # Scroll to bottom
        self.msg_canvas.yview_moveto(1.0)

    def _on_enter(self, event):
        if event.state & 0x1:  # Shift held → newline
            return
        self._send_message()
        return "break"

    def _send_message(self):
        text = self.input_entry.get("1.0", "end").strip()
        if not text:
            return
        if not self.controller.current_session_id:
            self._new_chat()

        self.input_entry.delete("1.0", "end")
        self._append_message("user", text)
        db.add_message(self.controller.current_session_id, "user", text)

        # Auto-title from first message
        msgs = db.get_messages(self.controller.current_session_id)
        if len(msgs) == 1:
            title = text[:40] + ("…" if len(text) > 40 else "")
            db.update_session_title(self.controller.current_session_id, title)
            self._refresh_sessions()

        # Disable send while waiting
        self.send_btn.config(state="disabled", text="…")
        self.input_entry.config(state="disabled")

        def call_ai():
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in db.get_messages(self.controller.current_session_id)
            ]
            reply = groq_service.chat(self.controller.current_ai, history)
            self.after(0, lambda: self._on_ai_reply(reply))

        threading.Thread(target=call_ai, daemon=True).start()

    def _on_ai_reply(self, reply: str):
        self._append_message("assistant", reply)
        db.add_message(self.controller.current_session_id, "assistant", reply)
        self.send_btn.config(state="normal", text="Send")
        self.input_entry.config(state="normal")
        self.input_entry.focus_set()
        self._refresh_sessions()
        
