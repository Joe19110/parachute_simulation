"""
ui/style.py
-----------
All ttk.Style configuration for the dark futuristic theme.
Call configure_styles(style) once after creating the ttk.Style object.
"""
import theme as T


def configure_styles(style):
    """Apply the full dark ttk style to *style*."""
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Base defaults
    style.configure(
        ".",
        background=T.BG_DARK,
        foreground=T.TEXT_PRIMARY,
        fieldbackground=T.BG_INPUT,
        borderwidth=0,
        font=("Segoe UI", 10),
    )

    # Notebook
    style.configure(
        "TNotebook",
        background=T.BG_DARK,
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=T.BG_PANEL,
        foreground=T.TEXT_SECONDARY,
        padding=(10, 4),
        font=("Segoe UI", 10),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", T.BG_CARD), ("active", T.BG_CARD)],
        foreground=[("selected", T.ACCENT_CYAN), ("active", T.TEXT_PRIMARY)],
    )

    # Frames & labels
    style.configure("TFrame",  background=T.BG_DARK)
    style.configure("TLabel",  background=T.BG_DARK, foreground=T.TEXT_PRIMARY)
    style.configure(
        "TLabelframe",
        background=T.BG_PANEL,
        foreground=T.ACCENT_CYAN,
        bordercolor=T.BORDER,
        borderwidth=1,
        relief="solid",
        padding=(8, 6),
    )
    style.configure(
        "TLabelframe.Label",
        background=T.BG_PANEL,
        foreground=T.ACCENT_CYAN,
        font=("Segoe UI", 10, "bold"),
    )

    # Inputs
    style.configure(
        "TEntry",
        fieldbackground=T.BG_INPUT,
        foreground=T.TEXT_PRIMARY,
        insertcolor=T.TEXT_PRIMARY,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TCombobox",
        fieldbackground=T.BG_INPUT,
        foreground=T.TEXT_PRIMARY,
        background=T.BG_INPUT,
        selectbackground=T.ACCENT_CYAN,
        selectforeground=T.BG_DARK,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", T.BG_INPUT)],
        foreground=[("readonly", T.TEXT_PRIMARY)],
    )

    # Radio / check / scale
    style.configure(
        "TRadiobutton",
        background=T.BG_PANEL,
        foreground=T.TEXT_PRIMARY,
        font=("Segoe UI", 10),
    )
    style.map("TRadiobutton", background=[("active", T.BG_CARD)])
    
    style.configure(
        "TCheckbutton",
        background=T.BG_PANEL,
        foreground=T.TEXT_PRIMARY,
        font=("Segoe UI", 10),
    )
    style.map("TCheckbutton", background=[("active", T.BG_CARD)])
    style.configure("TScale", background=T.BG_PANEL, troughcolor=T.BG_INPUT)

    # Named label variants
    style.configure(
        "Title.TLabel",
        font=("Segoe UI", 16, "bold"),
        foreground=T.ACCENT_CYAN,
        background=T.BG_DARK,
    )
    style.configure(
        "Sub.TLabel",
        foreground=T.TEXT_SECONDARY,
        background=T.BG_DARK,
        font=("Segoe UI", 9),
    )

    # Buttons
    _btn_specs = [
        ("Run.TButton",   T.ACCENT_CYAN,   T.BG_DARK),
        ("Pause.TButton", T.ACCENT_ORANGE, T.BG_DARK),
        ("Quit.TButton",  T.ACCENT_RED,    T.TEXT_PRIMARY),
        ("Reset.TButton", T.BORDER,        T.TEXT_PRIMARY),
        ("Jump.TButton",  T.ACCENT_YELLOW, T.BG_DARK),
    ]
    for name, bg, fg in _btn_specs:
        style.configure(
            name,
            background=bg,
            foreground=fg,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=6,
        )
        style.map(name, background=[("active", bg)])
