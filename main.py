#!/usr/bin/env python3
"""
AI Assistant Hub
────────────────
A modern multi-persona AI application built with:
  • Tkinter  – clean glassmorphism-inspired UI
  • Groq API – fast LLM responses
  • PostgreSQL – persistent users, chats & history
  • Turtle   – optional decorative splash graphics

Features
────────
• Login / Register with email verification code
• Five specialized AI assistants (Tax, Professional, Coding, Food, Travel)
• Per-AI chat consoles with automatic history
• Pin & delete chats
• Smooth navigation between all screens

Setup
─────
1. Copy .env.example → .env and fill in GROQ_API_KEY + SMTP credentials
2. Ensure PostgreSQL is running (default credentials in .env.example)
3. pip install -r requirements.txt
4. python main.py
"""

import sys
import os

# Make sure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.database import db
from ui.app import AIAssistantApp


def run_turtle_splash():
    """Optional short turtle animation for a warm welcome (non-blocking spirit)."""
    try:
        import turtle
        import time

        screen = turtle.Screen()
        screen.setup(420, 320)
        screen.bgcolor("#0b0b14")
        screen.title("AI Assistant Hub")
        screen.tracer(0)

        pen = turtle.Turtle()
        pen.hideturtle()
        pen.speed(0)
        pen.pensize(2)

        colors = ["#a78bfa", "#60a5fa", "#34d399", "#fbbf24", "#f472b6"]

        # Draw soft concentric arcs
        for i, color in enumerate(colors):
            pen.penup()
            pen.goto(0, -40 - i * 12)
            pen.pendown()
            pen.color(color)
            pen.circle(50 + i * 14, 180)
            screen.update()
            time.sleep(0.08)

        pen.penup()
        pen.goto(0, 20)
        pen.color("#e8e8f0")
        pen.write("AI Assistant Hub", align="center", font=("Segoe UI", 18, "bold"))
        screen.update()
        time.sleep(1.2)
        screen.bye()
    except Exception:
        # Turtle may fail in headless environments – silently skip
        pass


def main():
    print("🚀 Starting AI Assistant Hub…")
    try:
        db.init_schema()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and .env credentials are correct.")
        sys.exit(1)

    # Optional splash (comment out if you prefer instant start)
    # run_turtle_splash()

    app = AIAssistantApp()
    app.mainloop()


if __name__ == "__main__":
    main()
