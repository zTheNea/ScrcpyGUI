"""Reusable UI helper widget builders for ScrcpyGUI."""
from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional
import customtkinter as ctk
from presets import COLORS


class CTooltip:
    """Lightweight floating tooltip for CustomTkinter widgets."""

    def __init__(self, widget: Any, text: str, delay_ms: int = 350):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: Any = None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, _event: Any = None) -> None:
        self._cancel()
        self._hide()

    def _cancel(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 15
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)
            frame = ctk.CTkFrame(
                tw,
                fg_color=COLORS["card"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=6,
            )
            frame.pack()
            ctk.CTkLabel(
                frame,
                text=self.text,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text"],
                justify="left",
                padx=8,
                pady=4,
            ).pack()
        except Exception:
            pass

    def _hide(self) -> None:
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


def cfg_group(parent: ctk.CTkFrame, title: str, col: int) -> ctk.CTkFrame:
    """Create a grid column container with a header."""
    f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
    f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
    ctk.CTkLabel(
        f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]
    ).pack(fill="x", padx=10, pady=(10, 6))
    return f


def cfg_group_full(parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
    """Create a full-width packed container with a header."""
    f = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
    f.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(
        f, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]
    ).pack(fill="x", padx=10, pady=(10, 6))
    return f


def cfg_option_menu(
    parent: ctk.CTkFrame,
    label: str,
    var: ctk.StringVar,
    values: list[str],
    command: Optional[Callable[[str], None]] = None,
    tooltip: Optional[str] = None,
) -> ctk.CTkOptionMenu:
    """Create an option dropdown menu with a label and optional tooltip."""
    lbl = ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text2"])
    lbl.pack(anchor="w", padx=12, pady=(6, 0))
    cmd = command if command is not None else (lambda _: None)
    m = ctk.CTkOptionMenu(
        parent,
        variable=var,
        values=values,
        width=180,
        height=28,
        font=ctk.CTkFont(size=12),
        fg_color=COLORS["card"],
        button_color=COLORS["border"],
        button_hover_color=COLORS["card_hover"],
        command=cmd,
    )
    m.pack(padx=12, pady=(2, 4), anchor="w")
    if tooltip:
        CTooltip(lbl, tooltip)
        CTooltip(m, tooltip)
    return m


def cfg_entry(
    parent: ctk.CTkFrame,
    label: str,
    var: ctk.StringVar,
    on_change: Optional[Callable[..., Any]] = None,
    tooltip: Optional[str] = None,
) -> ctk.CTkEntry:
    """Create a text entry field with a label and optional trace update."""
    lbl = ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text2"])
    lbl.pack(anchor="w", padx=12, pady=(6, 0))
    e = ctk.CTkEntry(
        parent,
        textvariable=var,
        width=180,
        height=28,
        font=ctk.CTkFont(size=12),
        fg_color=COLORS["card"],
        border_color=COLORS["border"],
    )
    e.pack(padx=12, pady=(2, 4), anchor="w")
    if on_change is not None:
        var.trace_add("write", lambda *_: on_change())
    if tooltip:
        CTooltip(lbl, tooltip)
        CTooltip(e, tooltip)
    return e


def cfg_slider(
    parent: ctk.CTkFrame,
    label: str,
    var: ctk.IntVar,
    from_: int,
    to: int,
    on_change: Optional[Callable[..., Any]] = None,
    tooltip: Optional[str] = None,
) -> ctk.CTkSlider:
    """Create an integer slider with real-time numeric badge."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(6, 4))
    lbl = ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text2"])
    lbl.pack(side="left")
    val_label = ctk.CTkLabel(
        row, text=str(var.get()), font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["accent"], width=40
    )
    val_label.pack(side="right")

    def on_slide(v: float) -> None:
        val = int(float(v))
        var.set(val)
        val_label.configure(text=str(val))
        if on_change is not None:
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
    if tooltip:
        CTooltip(lbl, tooltip)
        CTooltip(s, tooltip)
    return s


def cfg_switch(
    parent: ctk.CTkFrame,
    label: str,
    var: ctk.BooleanVar,
    command: Optional[Callable[..., Any]] = None,
    tooltip: Optional[str] = None,
) -> ctk.CTkSwitch:
    """Create a toggle switch with label and optional tooltip."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(4, 2))
    lbl = ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text2"])
    lbl.pack(side="left")
    cmd = command if command is not None else (lambda: None)
    sw = ctk.CTkSwitch(row, text="", variable=var, width=40, progress_color=COLORS["accent"], command=cmd)
    sw.pack(side="right")
    if tooltip:
        CTooltip(lbl, tooltip)
        CTooltip(sw, tooltip)
    return sw



class InlineAppPicker(ctk.CTkFrame):
    """Integrated Inline Searchable App Selector (no popup window)."""

    def __init__(
        self,
        parent: Any,
        on_select: Callable[[str, str], None],
        selected_pkg_var: Optional[ctk.StringVar] = None,
        height: int = 150,
        **kwargs: Any,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_select = on_select
        self.selected_pkg_var = selected_pkg_var
        self.apps_list: list[tuple[str, str]] = []
        self.filtered_apps: list[tuple[str, str]] = []
        self._list_height = height

        # Search Bar Row
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 6))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_entry = ctk.CTkEntry(
            search_row,
            textvariable=self.search_var,
            placeholder_text="🔍 Filtrar app por nombre o paquete...",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_clear = ctk.CTkButton(
            search_row,
            text="🖥️ Escritorio Libre",
            width=125,
            height=32,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["card_hover"],
            command=lambda: self._select("", "Ninguna"),
        )
        self.btn_clear.pack(side="right")

        # Scrollable List of Apps
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            height=self._list_height,
        )
        self.list_frame.pack(fill="both", expand=True)

        self._render_empty("Conecta un dispositivo para cargar las aplicaciones.")

    def set_apps(self, apps: list[tuple[str, str]]) -> None:
        """Update the internal app list and refresh the display."""
        self.apps_list = list(apps)
        self._on_search_change()

    def set_loading(self, text: str = "⌛ Obteniendo aplicaciones del móvil...") -> None:
        """Display a loading state inside the picker list."""
        self._render_empty(text)

    def _render_empty(self, text: str) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.list_frame,
            text=text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted"],
        ).pack(pady=16)

    def _on_search_change(self, *args: Any) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_apps = list(self.apps_list)
        else:
            self.filtered_apps = [
                (name, pkg)
                for name, pkg in self.apps_list
                if query in name.lower() or query in pkg.lower()
            ]
        self._render_items()

    def _render_items(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not self.filtered_apps:
            msg = (
                "No hay aplicaciones instaladas detectadas."
                if not self.apps_list
                else "No se encontraron apps coincidentes."
            )
            self._render_empty(msg)
            return

        current_selected = self.selected_pkg_var.get().strip() if self.selected_pkg_var else ""

        _MAX_VISIBLE = 60
        total_filtered = len(self.filtered_apps)
        for name, pkg in self.filtered_apps[:_MAX_VISIBLE]:
            is_active = (pkg == current_selected) and bool(pkg)
            card_bg = COLORS["card_hover"] if is_active else COLORS["bg"]
            border_c = COLORS["accent"] if is_active else COLORS["border"]

            card = ctk.CTkFrame(
                self.list_frame,
                fg_color=card_bg,
                corner_radius=6,
                border_width=1,
                border_color=border_c,
                height=34,
                cursor="hand2",
            )
            card.pack(fill="x", pady=2, padx=2)
            card.pack_propagate(False)

            icon = "⭐" if is_active else "📱"
            ctk.CTkLabel(
                card,
                text=f"{icon} {name}",
                font=ctk.CTkFont(size=11, weight="bold" if is_active else "normal"),
                text_color=COLORS["accent"] if is_active else COLORS["text"],
                anchor="w",
            ).pack(side="left", padx=(8, 4))

            ctk.CTkLabel(
                card,
                text=f"({pkg})",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["muted"],
                anchor="w",
            ).pack(side="left", padx=(0, 6))

            if is_active:
                ctk.CTkLabel(
                    card,
                    text="SELECCIONADA",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["green"],
                ).pack(side="right", padx=(0, 8))

            def make_handler(p: str, n: str, c: ctk.CTkFrame):
                def on_click(_: Any = None):
                    self._select(p, n)

                def on_enter(_: Any = None):
                    if not (self.selected_pkg_var and self.selected_pkg_var.get() == p):
                        c.configure(fg_color=COLORS["card_hover"], border_color=COLORS["accent"])

                def on_leave(_: Any = None):
                    if not (self.selected_pkg_var and self.selected_pkg_var.get() == p):
                        c.configure(fg_color=COLORS["bg"], border_color=COLORS["border"])

                return on_click, on_enter, leave_cb

            click_cb, enter_cb, leave_cb = make_handler(pkg, name, card)

            card.bind("<Button-1>", click_cb)
            card.bind("<Enter>", enter_cb)
            card.bind("<Leave>", leave_cb)

            for child in card.winfo_children():
                child.bind("<Button-1>", click_cb)

        # Badge when list is truncated
        if total_filtered > _MAX_VISIBLE:
            ctk.CTkLabel(
                self.list_frame,
                text=f"Mostrando {_MAX_VISIBLE} de {total_filtered} apps — refina la búsqueda para ver más",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["muted"],
            ).pack(pady=(4, 8))


    def _select(self, pkg: str, name: str) -> None:
        if self.selected_pkg_var:
            self.selected_pkg_var.set(pkg)
        self._render_items()
        self.on_select(pkg, name)

    def set_state(self, state: str) -> None:
        """Enable or disable search entry and clear button."""
        try:
            self.search_entry.configure(state=state)
            self.btn_clear.configure(state=state)
        except Exception:
            pass
