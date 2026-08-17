"""Reusable UI helper widget builders for ScrcpyGUI."""
from __future__ import annotations

from typing import Any, Callable
import customtkinter as ctk
from presets import COLORS


def cfg_group(parent: ctk.CTkFrame, title: str, col: int) -> ctk.CTkFrame:
    """Create a grid column container with a header."""
    f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10)
    f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
    ctk.CTkLabel(
        f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]
    ).pack(fill="x", padx=10, pady=(10, 6))
    return f


def cfg_group_full(parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
    """Create a full-width packed container with a header."""
    f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10)
    f.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(
        f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]
    ).pack(fill="x", padx=10, pady=(10, 6))
    return f


def cfg_option_menu(
    parent: ctk.CTkFrame, label: str, var: ctk.StringVar, values: list[str], command: Callable[[str], None]
) -> ctk.CTkOptionMenu:
    """Create an option dropdown menu with a label."""
    ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(
        anchor="w", padx=12, pady=(6, 0)
    )
    m = ctk.CTkOptionMenu(
        parent,
        variable=var,
        values=values,
        width=180,
        fg_color=COLORS["card"],
        button_color=COLORS["border"],
        command=command,
    )
    m.pack(padx=12, pady=(2, 4), anchor="w")
    return m


def cfg_entry(
    parent: ctk.CTkFrame, label: str, var: ctk.StringVar, on_change: Callable[..., Any]
) -> ctk.CTkEntry:
    """Create a text entry field with a label and trace update."""
    ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(
        anchor="w", padx=12, pady=(6, 0)
    )
    e = ctk.CTkEntry(parent, textvariable=var, width=180, fg_color=COLORS["card"], border_color=COLORS["border"])
    e.pack(padx=12, pady=(2, 4), anchor="w")
    var.trace_add("write", lambda *_: on_change())
    return e


def cfg_slider(
    parent: ctk.CTkFrame, label: str, var: ctk.IntVar, from_: int, to: int, on_change: Callable[..., Any]
) -> ctk.CTkSlider:
    """Create an integer slider with real-time numeric badge."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(6, 4))
    ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
    val_label = ctk.CTkLabel(
        row, text=str(var.get()), font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"], width=40
    )
    val_label.pack(side="right")

    def on_slide(v: float) -> None:
        val = int(float(v))
        var.set(val)
        val_label.configure(text=str(val))
        on_change()

    s = ctk.CTkSlider(
        parent,
        from_=from_,
        to=to,
        variable=var,
        width=180,
        command=on_slide,
        progress_color=COLORS["accent"],
        button_color=COLORS["accent"],
    )
    s.pack(padx=12, anchor="w")
    return s


def cfg_switch(
    parent: ctk.CTkFrame, label: str, var: ctk.BooleanVar, command: Callable[..., Any]
) -> ctk.CTkSwitch:
    """Create a toggle switch with label."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(4, 2))
    ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=COLORS["text2"]).pack(side="left")
    sw = ctk.CTkSwitch(row, text="", variable=var, width=40, progress_color=COLORS["accent"], command=command)
    sw.pack(side="right")
    return sw
