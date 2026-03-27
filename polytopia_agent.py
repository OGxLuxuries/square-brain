#!/usr/bin/env python3
"""
polytopia_agent.py — Polytopia strategy agent with screen overlay.

Usage
-----
    python polytopia_agent.py                      # interactive GUI overlay
    python polytopia_agent.py --tribe bardur       # pre-select tribe
    python polytopia_agent.py --image screen.png   # analyse a screenshot
    python polytopia_agent.py --cli                # headless CLI mode

The overlay is a semi-transparent, always-on-top window that displays
strategy recommendations in real time.  Users can update their tribe,
turn number, star count and game context via the form inputs.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Optional

# ── Strategy package ───────────────────────────────────────────────────────
from strategy.tribes import list_tribe_names, get_tribe
from strategy.advisor import GameState, StrategyAdvisor
from strategy.image_analyzer import ImageAnalyzer, _PIL_AVAILABLE


# ---------------------------------------------------------------------------
# CLI / headless mode
# ---------------------------------------------------------------------------

def run_cli(args: argparse.Namespace) -> None:
    """Run the agent as a command-line tool (no GUI)."""
    tribe_name = args.tribe or _prompt_tribe()
    tribe = get_tribe(tribe_name)
    if tribe is None:
        print(f"[ERROR] Unknown tribe '{tribe_name}'.")
        print("Available:", ", ".join(list_tribe_names()))
        sys.exit(1)

    image_context: Optional[str] = None
    nearby_resources: list[str] = []

    if args.image:
        if not _PIL_AVAILABLE:
            print("[WARN] Pillow not installed — skipping image analysis.")
        else:
            img_path = Path(args.image)
            if not img_path.exists():
                print(f"[WARN] Image file not found: {img_path}")
            else:
                analyzer = ImageAnalyzer(img_path).load()
                image_context = analyzer.describe()
                nearby_resources = analyzer.detect_resources()
                print("\n── Image Analysis ──")
                print(image_context)

    state = GameState(
        tribe_name=tribe_name,
        turn=args.turn,
        stars=args.stars,
        cities=args.cities,
        city_level=args.city_level,
        opponent_distance=args.opponent_distance,
        nearby_resources=nearby_resources,
        image_context=image_context,
    )

    advisor = StrategyAdvisor(state)
    print("\n" + advisor.summary())


def _prompt_tribe() -> str:
    """Prompt user to select a tribe interactively."""
    names = list_tribe_names()
    print("Select your tribe:")
    for i, name in enumerate(names, 1):
        print(f"  {i:>2}. {name}")
    while True:
        choice = input("Enter tribe name or number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                return names[idx].lower().replace(" ", "-")
        else:
            if get_tribe(choice) is not None:
                return choice.lower().replace(" ", "-")
        print("Invalid choice, try again.")


# ---------------------------------------------------------------------------
# GUI overlay (tkinter)
# ---------------------------------------------------------------------------

def run_gui(args: argparse.Namespace) -> None:
    """Launch the always-on-top screen overlay."""
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
    except ImportError:
        print("[ERROR] tkinter is not available. Run with --cli for headless mode.")
        sys.exit(1)

    root = tk.Tk()
    app = PolytopiOverlay(root, initial_tribe=args.tribe)
    root.mainloop()


class PolytopiOverlay:
    """
    Main overlay window.

    The window is semi-transparent, always on top, and shows strategy
    recommendations that update live as the user changes their inputs.
    """

    OVERLAY_ALPHA = 0.92     # 0.0 = invisible, 1.0 = opaque
    BG_COLOR = "#1a1a2e"     # Dark navy
    FG_COLOR = "#e0e0ff"     # Soft white/lavender
    ACCENT    = "#4fc3f7"    # Light blue accent
    HIGH_COLOR = "#ef9a9a"   # Red for high-priority items
    MED_COLOR  = "#fff176"   # Yellow for medium priority
    LOW_COLOR  = "#a5d6a7"   # Green for low priority
    FONT_MONO  = ("Courier New", 10)
    FONT_UI    = ("Segoe UI", 10)
    FONT_HEAD  = ("Segoe UI", 12, "bold")

    def __init__(self, root: "tk.Tk", initial_tribe: Optional[str] = None) -> None:
        import tkinter as tk
        from tkinter import ttk, filedialog, scrolledtext

        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.scrolledtext = scrolledtext

        self.root = root
        self.root.title("Polytopia Strategy Agent")
        self.root.configure(bg=self.BG_COLOR)
        self.root.attributes("-topmost", True)     # always on top
        self.root.attributes("-alpha", self.OVERLAY_ALPHA)
        self.root.resizable(True, True)

        self._image_path: Optional[Path] = None
        self._build_ui(initial_tribe)
        self._update_recommendations()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, initial_tribe: Optional[str]) -> None:
        tk = self.tk
        ttk = self.ttk

        # ── Title bar ──────────────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        title_frame.pack(fill="x", padx=8, pady=(8, 0))

        tk.Label(
            title_frame, text="🎮 Polytopia Strategy Agent",
            font=self.FONT_HEAD, bg=self.BG_COLOR, fg=self.ACCENT,
        ).pack(side="left")

        # Opacity slider
        tk.Label(
            title_frame, text="Opacity:", font=self.FONT_UI,
            bg=self.BG_COLOR, fg=self.FG_COLOR,
        ).pack(side="right", padx=(4, 0))
        self._alpha_var = tk.DoubleVar(value=self.OVERLAY_ALPHA)
        opacity_slider = ttk.Scale(
            title_frame, from_=0.3, to=1.0, orient="horizontal",
            variable=self._alpha_var, command=self._on_alpha_change, length=80,
        )
        opacity_slider.pack(side="right", padx=4)

        # ── Input panel ────────────────────────────────────────────────
        input_frame = tk.LabelFrame(
            self.root, text=" Game State ", font=self.FONT_UI,
            bg=self.BG_COLOR, fg=self.ACCENT, bd=1, relief="groove",
        )
        input_frame.pack(fill="x", padx=8, pady=6)

        # Row 0: Tribe selector
        tribe_names = list_tribe_names()
        tk.Label(input_frame, text="Tribe:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self._tribe_var = tk.StringVar(value=initial_tribe or tribe_names[0])
        tribe_combo = ttk.Combobox(
            input_frame, textvariable=self._tribe_var,
            values=tribe_names, state="readonly", width=16,
        )
        tribe_combo.grid(row=0, column=1, sticky="w", padx=4, pady=3)
        tribe_combo.bind("<<ComboboxSelected>>", lambda _: self._update_recommendations())

        # Row 1: Turn / Stars
        tk.Label(input_frame, text="Turn:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self._turn_var = tk.IntVar(value=1)
        tk.Spinbox(input_frame, from_=1, to=200, textvariable=self._turn_var,
                   width=5, command=self._update_recommendations,
                   bg="#2a2a3e", fg=self.FG_COLOR, buttonbackground="#3a3a5e",
                   ).grid(row=1, column=1, sticky="w", padx=4, pady=3)

        tk.Label(input_frame, text="Stars:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=1, column=2, sticky="w", padx=4, pady=3)
        self._stars_var = tk.IntVar(value=5)
        tk.Spinbox(input_frame, from_=0, to=999, textvariable=self._stars_var,
                   width=5, command=self._update_recommendations,
                   bg="#2a2a3e", fg=self.FG_COLOR, buttonbackground="#3a3a5e",
                   ).grid(row=1, column=3, sticky="w", padx=4, pady=3)

        # Row 2: Cities / City level
        tk.Label(input_frame, text="Cities:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self._cities_var = tk.IntVar(value=1)
        tk.Spinbox(input_frame, from_=1, to=50, textvariable=self._cities_var,
                   width=5, command=self._update_recommendations,
                   bg="#2a2a3e", fg=self.FG_COLOR, buttonbackground="#3a3a5e",
                   ).grid(row=2, column=1, sticky="w", padx=4, pady=3)

        tk.Label(input_frame, text="City lvl:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=2, column=2, sticky="w", padx=4, pady=3)
        self._city_level_var = tk.IntVar(value=1)
        tk.Spinbox(input_frame, from_=1, to=5, textvariable=self._city_level_var,
                   width=5, command=self._update_recommendations,
                   bg="#2a2a3e", fg=self.FG_COLOR, buttonbackground="#3a3a5e",
                   ).grid(row=2, column=3, sticky="w", padx=4, pady=3)

        # Row 3: Opponent distance
        tk.Label(input_frame, text="Opp. dist (turns):", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=3, column=0, sticky="w", padx=4, pady=3)
        self._opp_dist_var = tk.IntVar(value=5)
        tk.Spinbox(input_frame, from_=1, to=20, textvariable=self._opp_dist_var,
                   width=5, command=self._update_recommendations,
                   bg="#2a2a3e", fg=self.FG_COLOR, buttonbackground="#3a3a5e",
                   ).grid(row=3, column=1, sticky="w", padx=4, pady=3)

        # Row 4: Nearby resources checkboxes
        tk.Label(input_frame, text="Resources:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=4, column=0, sticky="w", padx=4, pady=3)
        resources_frame = tk.Frame(input_frame, bg=self.BG_COLOR)
        resources_frame.grid(row=4, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        self._resource_vars: dict[str, "tk.BooleanVar"] = {}
        for i, res in enumerate(["forest", "fish", "farm", "mountain", "animal"]):
            var = tk.BooleanVar()
            self._resource_vars[res] = var
            tk.Checkbutton(
                resources_frame, text=res.capitalize(), variable=var,
                bg=self.BG_COLOR, fg=self.FG_COLOR, selectcolor="#3a3a5e",
                activebackground=self.BG_COLOR, activeforeground=self.FG_COLOR,
                command=self._update_recommendations,
            ).pack(side="left", padx=2)

        # Row 5: Researched techs
        tk.Label(input_frame, text="Researched techs:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=5, column=0, sticky="w", padx=4, pady=3)
        self._techs_var = tk.StringVar()
        tk.Entry(
            input_frame, textvariable=self._techs_var,
            bg="#2a2a3e", fg=self.FG_COLOR, insertbackground=self.FG_COLOR, width=30,
        ).grid(row=5, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        tk.Label(input_frame, text="(comma separated)", bg=self.BG_COLOR, fg="#888",
                 font=("Segoe UI", 8)).grid(row=6, column=1, columnspan=3, sticky="w", padx=4)
        self._techs_var.trace_add("write", lambda *_: self._update_recommendations())

        # Row 7: Image upload
        tk.Label(input_frame, text="Screenshot:", bg=self.BG_COLOR, fg=self.FG_COLOR,
                 font=self.FONT_UI).grid(row=7, column=0, sticky="w", padx=4, pady=3)
        img_frame = tk.Frame(input_frame, bg=self.BG_COLOR)
        img_frame.grid(row=7, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        self._img_label = tk.Label(img_frame, text="No image loaded", bg=self.BG_COLOR,
                                   fg="#888", font=self.FONT_UI)
        self._img_label.pack(side="left")
        tk.Button(
            img_frame, text="Browse…", command=self._load_image,
            bg="#3a3a5e", fg=self.FG_COLOR, relief="flat", padx=6,
        ).pack(side="left", padx=(6, 0))

        # ── Recommendation output ──────────────────────────────────────
        out_frame = tk.LabelFrame(
            self.root, text=" Recommendations ", font=self.FONT_UI,
            bg=self.BG_COLOR, fg=self.ACCENT, bd=1, relief="groove",
        )
        out_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._output = self.scrolledtext.ScrolledText(
            out_frame, wrap="word", font=self.FONT_MONO,
            bg="#0d0d1a", fg=self.FG_COLOR, insertbackground=self.FG_COLOR,
            relief="flat", height=18, width=60,
        )
        self._output.pack(fill="both", expand=True, padx=4, pady=4)

        # Tag colours for priority colouring
        self._output.tag_configure("high",   foreground=self.HIGH_COLOR, font=(*self.FONT_MONO[:2], "bold"))
        self._output.tag_configure("medium", foreground=self.MED_COLOR)
        self._output.tag_configure("low",    foreground=self.LOW_COLOR)
        self._output.tag_configure("header", foreground=self.ACCENT, font=(*self.FONT_MONO[:2], "bold"))
        self._output.tag_configure("label",  foreground="#aaa")
        self._output.tag_configure("choice_grow",  foreground="#81c784", font=(*self.FONT_MONO[:2], "bold"))
        self._output.tag_configure("choice_hold",  foreground="#ffb74d", font=(*self.FONT_MONO[:2], "bold"))

        # ── Update button ──────────────────────────────────────────────
        tk.Button(
            self.root, text="↻  Refresh Recommendations",
            command=self._update_recommendations,
            bg="#4a4a7e", fg=self.FG_COLOR, relief="flat",
            font=self.FONT_UI, padx=10, pady=6,
        ).pack(pady=(0, 8))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_alpha_change(self, val: str) -> None:
        self.root.attributes("-alpha", float(val))

    def _load_image(self) -> None:
        path = self.filedialog.askopenfilename(
            title="Select Polytopia screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All", "*.*")],
        )
        if path:
            self._image_path = Path(path)
            self._img_label.config(text=self._image_path.name, fg=self.FG_COLOR)
            self._update_recommendations()

    def _update_recommendations(self, *_args) -> None:
        """Rebuild the recommendation text from current inputs."""
        tribe_name = self._tribe_var.get().lower().replace(" ", "-")

        nearby = [r for r, v in self._resource_vars.items() if v.get()]
        techs_raw = self._techs_var.get().strip()
        techs = [t.strip() for t in techs_raw.split(",") if t.strip()] if techs_raw else []

        image_context: Optional[str] = None
        if self._image_path and self._image_path.exists() and _PIL_AVAILABLE:
            try:
                analyzer = ImageAnalyzer(self._image_path).load()
                image_context = analyzer.describe()
                # Auto-populate resources from image if none selected
                if not nearby:
                    nearby = analyzer.detect_resources()
                    for res, var in self._resource_vars.items():
                        var.set(res in nearby)
            except Exception as exc:
                image_context = f"(Image analysis failed: {exc})"

        state = GameState(
            tribe_name=tribe_name,
            turn=self._turn_var.get(),
            stars=self._stars_var.get(),
            cities=self._cities_var.get(),
            city_level=self._city_level_var.get(),
            has_tech=techs,
            opponent_distance=self._opp_dist_var.get(),
            nearby_resources=nearby,
            image_context=image_context,
        )

        try:
            advisor = StrategyAdvisor(state)
        except ValueError as exc:
            self._set_output(str(exc))
            return

        self._render_summary(advisor, image_context)

    def _render_summary(self, advisor: StrategyAdvisor, image_context: Optional[str]) -> None:
        """Render coloured recommendations in the output widget."""
        st = self._output
        st.config(state="normal")
        st.delete("1.0", "end")

        tribe = advisor.tribe
        s = advisor.state
        recs = advisor.recommend()
        choice, reason = advisor.stars_vs_borders()
        next_tech = advisor.best_next_tech()

        def _write(text: str, tag: Optional[str] = None) -> None:
            if tag:
                st.insert("end", text, tag)
            else:
                st.insert("end", text)

        _write(f"═══ {tribe.name} — Turn {s.turn} ═══\n", "header")
        _write(f"Stars: {s.stars}★  Cities: {s.cities}  Level: {s.city_level}\n", "label")
        _write("\n")

        # Stars vs borders
        _write("★ STARS vs BORDERS → ", "label")
        if choice == "grow_city":
            _write("GROW CITY BORDERS\n", "choice_grow")
        else:
            _write("HOLD STARS\n", "choice_hold")
        _write(f"  {reason}\n\n")

        # Next tech
        if next_tech:
            _write(f"NEXT TECH: {next_tech} (5★)\n", "header")
            _write(f"  {tribe.strategy_notes[:140].rstrip()}…\n\n")

        # Recommendations
        _write("RECOMMENDATIONS:\n", "header")
        colour_map = {"high": "high", "medium": "medium", "low": "low"}
        for i, rec in enumerate(recs[:6], 1):
            tag = colour_map.get(rec.priority, "")
            cost = f" [{rec.stars_cost}★]" if rec.stars_cost else ""
            _write(f"  {i}. [{rec.priority.upper()}] {rec.category.capitalize()} — "
                   f"{rec.action}{cost}\n", tag)
            # wrap the rationale
            wrapped = textwrap.fill(rec.rationale, width=56,
                                    initial_indent="     → ", subsequent_indent="       ")
            _write(f"{wrapped}\n\n")

        # Image context
        if image_context:
            _write("── Image Analysis ──\n", "header")
            _write(f"{image_context}\n")

        st.config(state="disabled")

    def _set_output(self, text: str) -> None:
        st = self._output
        st.config(state="normal")
        st.delete("1.0", "end")
        st.insert("end", text)
        st.config(state="disabled")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Polytopia Strategy Agent — overlay advisor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python polytopia_agent.py
              python polytopia_agent.py --tribe bardur --turn 3 --stars 12
              python polytopia_agent.py --image screenshot.png --cli
        """),
    )
    p.add_argument("--cli", action="store_true",
                   help="Run in headless CLI mode (no GUI)")
    p.add_argument("--tribe", default=None,
                   help="Tribe name (e.g. bardur, oumaji, kickoo)")
    p.add_argument("--image", default=None, metavar="FILE",
                   help="Path to a Polytopia screenshot for image analysis")
    p.add_argument("--turn", type=int, default=1, metavar="N",
                   help="Current turn number (default: 1)")
    p.add_argument("--stars", type=int, default=5, metavar="N",
                   help="Stars available this turn (default: 5)")
    p.add_argument("--cities", type=int, default=1, metavar="N",
                   help="Number of cities (default: 1)")
    p.add_argument("--city-level", type=int, default=1, dest="city_level", metavar="N",
                   help="Average city level (default: 1)")
    p.add_argument("--opponent-distance", type=int, default=5, dest="opponent_distance",
                   metavar="N",
                   help="Estimated turns until first contact (default: 5)")
    return p


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        run_gui(args)


if __name__ == "__main__":
    main()
