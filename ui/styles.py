"""
Shared styles, colors, and helper functions for a modern glassmorphism-inspired UI.
Tkinter has limited true transparency, so we approximate with layered colors,
soft borders, and careful spacing.
"""

# Color palette – deep dark with soft accents
COLORS = {
    "bg": "#0b0b14",
    "bg_secondary": "#12121f",
    "card": "#16162a",
    "card_hover": "#1c1c35",
    "glass": "#1a1a2e",
    "border": "#2a2a45",
    "border_light": "#3a3a5c",
    "text": "#e8e8f0",
    "text_muted": "#9898b0",
    "text_dim": "#6a6a80",
    "accent": "#a78bfa",
    "accent_hover": "#c4b5fd",
    "success": "#34d399",
    "danger": "#f87171",
    "warning": "#fbbf24",
    "input_bg": "#0f0f1c",
    "sidebar": "#0e0e1a",
}

FONTS = {
    "title": ("Segoe UI", 28, "bold"),
    "heading": ("Segoe UI", 18, "bold"),
    "subheading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 10),
    "mono": ("Consolas", 11),
    "button": ("Segoe UI", 11, "bold"),
}


def rounded_rect(canvas, x1, y1, x2, y2, radius=12, **kwargs):
    """Draw a rounded rectangle on a Canvas (approximation)."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)
