"""
ARI'Lab: Advanced Review Intelligence Lab

A code review training simulator. Each session presents a series of
buggy or poorly written Python snippets. You read the code, identify
the problem, write a review comment, and ARI'Lab scores your answer
against a set of accepted keywords the way a senior developer would
evaluate a junior's first pull request.

The five challenge categories mirror the issues that come up most
often in real code reviews: logic bugs, security vulnerabilities,
performance problems, code smells, and exception handling. Getting
good at spotting these is what separates a junior developer from
someone who is genuinely useful on a production codebase from day one.


Architecture:
    The challenge bank lives in challenges.py as a plain list of dicts.
    The scoring engine lives in scorer.py and is completely independent
    of the GUI, you could swap the Tkinter front end for a web app
    without touching the scoring logic.
    Session state is tracked in memory and written to SQLite at the end
    of each challenge so results persist across sessions.
"""

import tkinter as tk
from tkinter import scrolledtext
import random
from datetime import datetime
from challenges import CHALLENGES
from scorer import score_answer
from database import init_db, log_result, get_session_summary

# How many challenges make up one session.
# Ten gives enough variety to cover multiple categories without
# the session feeling too long for a demo.
SESSION_LENGTH = 10

# Colour palette.
# The split-screen design uses dark on the left for the code panel
# and light on the right for the review panel. The contrast is
# intentional: it mirrors how a real IDE and PR review tool sit
# side by side on a developer's screen.
CODE_BG       = "#1E1E2E"   # code panel background, dark, editor-like
CODE_FG       = "#CDD6F4"   # default code text
LINE_NUM_FG   = "#45475A"   # line number gutter colour
TAB_BG        = "#181825"   # file tab bar background
TAB_FG        = "#CDD6F4"   # file tab text

REVIEW_BG     = "#FFFFFF"   # review panel background, clean white
REVIEW_FG     = "#1A1A2E"   # review panel text
PANEL_BG      = "#F5F5F5"   # metadata section background
BORDER        = "#E0E0E0"   # divider lines

GREEN         = "#40A02B"   # correct / full marks
AMBER         = "#FE640B"   # partial credit
RED           = "#D20F39"   # wrong answer
BLUE          = "#1E66F5"   # accent — submit button, highlights
DIM           = "#888899"   # secondary text

# Syntax highlight colours for the code panel.
# Applied manually since we're not using an external library.
# Covers the most visually distinct token types — keywords,
# strings, comments, and numbers. Everything else stays as CODE_FG.
SYN_KEYWORD   = "#CBA6F7"   # purple — def, if, for, return etc
SYN_STRING    = "#A6E3A1"   # green — string literals
SYN_COMMENT   = "#6C7086"   # grey — inline comments
SYN_NUMBER    = "#FAB387"   # orange — numeric literals
SYN_BUILTIN   = "#89DCEB"   # cyan — print, len, range etc

PYTHON_KEYWORDS = {
    "def", "class", "if", "else", "elif", "for", "while", "return",
    "import", "from", "try", "except", "finally", "with", "as",
    "in", "not", "and", "or", "is", "True", "False", "None",
    "pass", "break", "continue", "raise", "yield", "lambda",
    "global", "nonlocal", "assert", "del",
}

PYTHON_BUILTINS = {
    "print", "len", "range", "int", "str", "float", "list",
    "dict", "set", "tuple", "type", "isinstance", "hasattr",
    "getattr", "setattr", "open", "input", "enumerate", "zip",
    "map", "filter", "sorted", "reversed", "sum", "min", "max",
}

DIFFICULTY_COLORS = {
    "JUNIOR": GREEN,
    "MID":    AMBER,
    "SENIOR": RED,
}

CATEGORY_ICONS = {
    "Logic Bug":           "◈",
    "Security":            "⚠",
    "Performance":         "⟳",
    "Code Smell":          "✦",
    "Exception Handling":  "⊗",
}


class AriLabApp:
    """
    Main application. Manages the session lifecycle, the split-screen
    layout, syntax highlighting, answer submission, and result display.

    Session flow:
        1. _start_session() shuffles the challenge bank and picks
           SESSION_LENGTH challenges
        2. _load_challenge() displays the current challenge
        3. _apply_highlighting() colours the code tokens
        4. _submit() scores the answer and shows feedback
        5. _next_challenge() advances the session or ends it
        6. _show_summary() displays the final session results
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ARI'Lab")
        self.root.geometry("1300x780")
        self.root.minsize(1000, 600)
        self.root.configure(bg=CODE_BG)
        self.root.resizable(True, True)

        # Session state
        self.session_challenges = []   # the challenges for this session
        self.current_index      = 0    # which challenge we're on
        self.current_challenge  = None # the challenge dict currently displayed
        self.session_score      = 0    # cumulative score for this session
        self.session_results    = []   # list of result dicts for the summary
        self.answered           = False  # prevents multiple submits per challenge

        init_db()
        self._build_ui()
        self._start_session()

    def _start_session(self):
        """
        Picks SESSION_LENGTH challenges at random from the full bank,
        resets all session counters, and loads the first challenge.

        Shuffling the full bank rather than sampling means each session
        has a different order even if the same challenges appear across
        sessions. It also guarantees no duplicates within a session.
        """
        pool = CHALLENGES.copy()
        random.shuffle(pool)
        self.session_challenges = pool[:SESSION_LENGTH]
        self.current_index      = 0
        self.session_score      = 0
        self.session_results    = []
        self.answered           = False
        self._load_challenge(self.session_challenges[0])

    def _build_ui(self):
        """
        Builds the split-screen layout.

        Left side — code panel: tab bar, line numbers, syntax-highlighted code.
        Right side — review panel: challenge metadata, answer input, feedback.
        Bottom bar — session progress, score, streak.
        """

        # Top identity bar
        topbar = tk.Frame(self.root, bg=TAB_BG, height=44)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="ARI'Lab",
            font=("Consolas", 14, "bold"),
            bg=TAB_BG,
            fg=CODE_FG
        ).place(x=20, rely=0.5, anchor="w")

        tk.Label(
            topbar,
            text="Advanced Review Intelligence Lab",
            font=("Consolas", 9),
            bg=TAB_BG,
            fg=LINE_NUM_FG
        ).place(x=120, rely=0.5, anchor="w")

        self.session_lbl = tk.Label(
            topbar,
            text="",
            font=("Consolas", 9),
            bg=TAB_BG,
            fg=DIM
        )
        self.session_lbl.place(relx=1.0, x=-20, rely=0.5, anchor="e")

        # Main body — split horizontally
        body = tk.Frame(self.root, bg=CODE_BG)
        body.pack(fill=tk.BOTH, expand=True)

        # Left panel — code viewer
        left = tk.Frame(body, bg=CODE_BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # File tab bar — shows the simulated filename
        self.tab_bar = tk.Frame(left, bg=TAB_BG, height=32)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        self.file_tab = tk.Label(
            self.tab_bar,
            text="",
            font=("Consolas", 9),
            bg=CODE_BG,
            fg=CODE_FG,
            padx=16,
            pady=6
        )
        self.file_tab.pack(side=tk.LEFT)

        # Code area — line numbers + code text side by side
        code_area = tk.Frame(left, bg=CODE_BG)
        code_area.pack(fill=tk.BOTH, expand=True)

        # Line number gutter
        self.gutter = tk.Text(
            code_area,
            width=4,
            font=("Consolas", 12),
            bg=TAB_BG,
            fg=LINE_NUM_FG,
            relief=tk.FLAT,
            bd=0,
            state=tk.DISABLED,
            padx=6,
            pady=12,
            selectbackground=TAB_BG
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        # Code text widget — read-only, syntax highlighted
        self.code_text = tk.Text(
            code_area,
            font=("Consolas", 12),
            bg=CODE_BG,
            fg=CODE_FG,
            relief=tk.FLAT,
            bd=0,
            state=tk.DISABLED,
            padx=12,
            pady=12,
            wrap=tk.NONE,
            insertbackground=CODE_FG,
            selectbackground="#313244",
            selectforeground=CODE_FG
        )
        code_scroll_y = tk.Scrollbar(
            code_area, orient="vertical", command=self.code_text.yview)
        code_scroll_x = tk.Scrollbar(
            left, orient="horizontal", command=self.code_text.xview)
        self.code_text.configure(
            yscrollcommand=code_scroll_y.set,
            xscrollcommand=code_scroll_x.set)
        code_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        code_scroll_x.pack(fill=tk.X)

        # Syntax highlight tags
        self.code_text.tag_config("keyword",  foreground=SYN_KEYWORD)
        self.code_text.tag_config("string",   foreground=SYN_STRING)
        self.code_text.tag_config("comment",  foreground=SYN_COMMENT)
        self.code_text.tag_config("number",   foreground=SYN_NUMBER)
        self.code_text.tag_config("builtin",  foreground=SYN_BUILTIN)

        # Thin vertical divider between panels
        tk.Frame(body, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Right panel — review interface
        right = tk.Frame(body, bg=REVIEW_BG, width=440)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        # Challenge metadata section
        meta = tk.Frame(right, bg=PANEL_BG)
        meta.pack(fill=tk.X)

        self.category_lbl = tk.Label(
            meta,
            text="",
            font=("Arial", 10, "bold"),
            bg=PANEL_BG,
            fg=REVIEW_FG,
            anchor="w"
        )
        self.category_lbl.pack(anchor="w", padx=20, pady=(16, 2))

        self.difficulty_lbl = tk.Label(
            meta,
            text="",
            font=("Arial", 9),
            bg=PANEL_BG,
            fg=DIM,
            anchor="w"
        )
        self.difficulty_lbl.pack(anchor="w", padx=20)

        self.points_lbl = tk.Label(
            meta,
            text="",
            font=("Arial", 9),
            bg=PANEL_BG,
            fg=DIM,
            anchor="w"
        )
        self.points_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X)

        # Challenge description
        tk.Label(
            right,
            text="WHAT DO YOU SEE?",
            font=("Arial", 9, "bold"),
            bg=REVIEW_BG,
            fg=DIM,
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self.desc_lbl = tk.Label(
            right,
            text="",
            font=("Arial", 10),
            bg=REVIEW_BG,
            fg=REVIEW_FG,
            anchor="w",
            wraplength=390,
            justify=tk.LEFT
        )
        self.desc_lbl.pack(anchor="w", padx=20, pady=(0, 12))

        # Answer input
        tk.Label(
            right,
            text="YOUR REVIEW COMMENT",
            font=("Arial", 9, "bold"),
            bg=REVIEW_BG,
            fg=DIM,
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(4, 4))

        tk.Label(
            right,
            text="Write what you would say in a pull request review.",
            font=("Arial", 8),
            bg=REVIEW_BG,
            fg=DIM,
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(0, 6))

        self.answer_box = tk.Text(
            right,
            font=("Arial", 10),
            bg=PANEL_BG,
            fg=REVIEW_FG,
            relief=tk.FLAT,
            bd=0,
            height=6,
            wrap=tk.WORD,
            padx=12,
            pady=10,
            insertbackground=REVIEW_FG
        )
        self.answer_box.pack(fill=tk.X, padx=20)

        # Submit button
        self.submit_btn = tk.Button(
            right,
            text="SUBMIT REVIEW",
            font=("Arial", 10, "bold"),
            bg=BLUE,
            fg="#FFFFFF",
            activebackground="#1A5CD4",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=20,
            pady=10,
            command=self._submit
        )
        self.submit_btn.pack(fill=tk.X, padx=20, pady=12)

        # Feedback section — hidden until answer is submitted
        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X, padx=20)

        self.feedback_frame = tk.Frame(right, bg=REVIEW_BG)
        self.feedback_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        self.score_result_lbl = tk.Label(
            self.feedback_frame,
            text="",
            font=("Arial", 13, "bold"),
            bg=REVIEW_BG,
            fg=REVIEW_FG,
            anchor="w"
        )
        self.score_result_lbl.pack(anchor="w", pady=(0, 8))

        tk.Label(
            self.feedback_frame,
            text="IDEAL REVIEW COMMENT",
            font=("Arial", 8, "bold"),
            bg=REVIEW_BG,
            fg=DIM,
            anchor="w"
        ).pack(anchor="w")

        self.ideal_lbl = tk.Label(
            self.feedback_frame,
            text="",
            font=("Arial", 9),
            bg=REVIEW_BG,
            fg=REVIEW_FG,
            anchor="w",
            wraplength=390,
            justify=tk.LEFT
        )
        self.ideal_lbl.pack(anchor="w", pady=(4, 12))

        tk.Label(
            self.feedback_frame,
            text="EXPLANATION",
            font=("Arial", 8, "bold"),
            bg=REVIEW_BG,
            fg=DIM,
            anchor="w"
        ).pack(anchor="w")

        self.explanation_lbl = tk.Label(
            self.feedback_frame,
            text="",
            font=("Arial", 9),
            bg=REVIEW_BG,
            fg=REVIEW_FG,
            anchor="w",
            wraplength=390,
            justify=tk.LEFT
        )
        self.explanation_lbl.pack(anchor="w", pady=(4, 16))

        self.next_btn = tk.Button(
            self.feedback_frame,
            text="NEXT CHALLENGE  →",
            font=("Arial", 10, "bold"),
            bg=REVIEW_BG,
            fg=BLUE,
            activebackground=PANEL_BG,
            activeforeground=BLUE,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=0,
            pady=8,
            command=self._next_challenge
        )

        # Bottom bar — session progress
        bottom = tk.Frame(self.root, bg=TAB_BG, height=32)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        self.progress_lbl = tk.Label(
            bottom,
            text="",
            font=("Consolas", 8),
            bg=TAB_BG,
            fg=DIM
        )
        self.progress_lbl.pack(side=tk.LEFT, padx=16, pady=6)

        self.score_lbl = tk.Label(
            bottom,
            text="Score: 0",
            font=("Consolas", 8, "bold"),
            bg=TAB_BG,
            fg=CODE_FG
        )
        self.score_lbl.pack(side=tk.RIGHT, padx=16)

        self.accuracy_lbl = tk.Label(
            bottom,
            text="Accuracy: —",
            font=("Consolas", 8),
            bg=TAB_BG,
            fg=DIM
        )
        self.accuracy_lbl.pack(side=tk.RIGHT, padx=8)

    def _load_challenge(self, challenge: dict):
        """
        Loads a challenge into the UI. Clears the previous challenge,
        populates the code panel and metadata, and resets the answer input.
        """
        self.current_challenge = challenge
        self.answered          = False

        # Update file tab
        self.file_tab.config(text=f"  {challenge['filename']}  ")

        # Populate code panel
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, challenge["code"])
        self._apply_highlighting()
        self.code_text.config(state=tk.DISABLED)

        # Populate line number gutter
        lines = challenge["code"].count("\n") + 1
        self.gutter.config(state=tk.NORMAL)
        self.gutter.delete("1.0", tk.END)
        for i in range(1, lines + 1):
            self.gutter.insert(tk.END, f"{i:>3}\n")
        self.gutter.config(state=tk.DISABLED)

        # Populate metadata
        icon = CATEGORY_ICONS.get(challenge["category"], "●")
        self.category_lbl.config(
            text=f"{icon}  {challenge['category'].upper()}")
        diff_color = DIFFICULTY_COLORS.get(challenge["difficulty"], DIM)
        self.difficulty_lbl.config(
            text=f"Difficulty: {challenge['difficulty']}",
            fg=diff_color)
        self.points_lbl.config(
            text=f"Points available: {challenge['points']}")
        self.desc_lbl.config(text=challenge["description"])

        # Reset answer area
        self.answer_box.config(state=tk.NORMAL)
        self.answer_box.delete("1.0", tk.END)
        self.submit_btn.config(state=tk.NORMAL, bg=BLUE)

        # Clear feedback from previous challenge
        self.score_result_lbl.config(text="")
        self.ideal_lbl.config(text="")
        self.explanation_lbl.config(text="")
        self.next_btn.pack_forget()

        # Update bottom bar
        idx = self.current_index + 1
        self.progress_lbl.config(
            text=f"Challenge {idx} of {SESSION_LENGTH}  |  "
                 f"{challenge['category']}  |  {challenge['difficulty']}")
        self.session_lbl.config(
            text=f"Session  {idx}/{SESSION_LENGTH}")

    def _apply_highlighting(self):
        """
        Applies syntax highlighting to the code in the code_text widget.
        Tokenises the code line by line, word by word, and applies colour
        tags for keywords, builtins, strings, comments, and numbers.

        This is a simplified tokeniser — it handles the most visually
        important token types without the complexity of a full parser.
        String detection handles both single and double quoted literals
        on a single line. Multi-line strings are not specially handled.
        """
        code = self.code_text.get("1.0", tk.END)
        lines = code.split("\n")

        for line_num, line in enumerate(lines, start=1):
            col = 0

            # Comments — everything from # to end of line
            stripped = line.lstrip()
            if stripped.startswith("#"):
                start = f"{line_num}.0"
                end   = f"{line_num}.{len(line)}"
                self.code_text.tag_add("comment", start, end)
                continue

            if "#" in line:
                comment_pos = line.index("#")
                start = f"{line_num}.{comment_pos}"
                end   = f"{line_num}.{len(line)}"
                self.code_text.tag_add("comment", start, end)
                line = line[:comment_pos]

            # String literals — simple single-line detection
            in_string    = False
            string_char  = None
            string_start = None

            i = 0
            while i < len(line):
                ch = line[i]

                if not in_string and ch in ('"', "'"):
                    in_string    = True
                    string_char  = ch
                    string_start = i
                elif in_string and ch == string_char:
                    start = f"{line_num}.{string_start}"
                    end   = f"{line_num}.{i + 1}"
                    self.code_text.tag_add("string", start, end)
                    in_string = False
                i += 1

            # Words — keywords, builtins, numbers
            import re
            for match in re.finditer(r'\b(\w+)\b', line):
                word  = match.group()
                start = f"{line_num}.{match.start()}"
                end   = f"{line_num}.{match.end()}"

                if word in PYTHON_KEYWORDS:
                    self.code_text.tag_add("keyword", start, end)
                elif word in PYTHON_BUILTINS:
                    self.code_text.tag_add("builtin", start, end)
                elif word.isdigit() or (
                        word.replace(".", "", 1).isdigit() and "." in word):
                    self.code_text.tag_add("number", start, end)

    def _submit(self):
        """
        Scores the user's answer against the current challenge.
        Prevents resubmission by disabling the submit button.
        Shows feedback immediately — score, ideal comment, explanation.
        Logs the result to SQLite.
        """
        if self.answered:
            return

        user_answer = self.answer_box.get("1.0", tk.END).strip()

        if not user_answer:
            self.score_result_lbl.config(
                text="Write a review comment first.", fg=AMBER)
            return

        self.answered = True
        challenge = self.current_challenge

        result = score_answer(user_answer, challenge)

        self.session_score += result["points_earned"]

        self.session_results.append({
            "challenge_id": challenge["id"],
            "category":     challenge["category"],
            "difficulty":   challenge["difficulty"],
            "points_avail": challenge["points"],
            "points_earned":result["points_earned"],
            "grade":        result["grade"],
        })

        # Show score result
        grade_colors = {"FULL": GREEN, "PARTIAL": AMBER, "WRONG": RED}
        grade_text = {
            "FULL":    f"✓  Full marks  +{result['points_earned']} pts",
            "PARTIAL": f"~  Partial credit  +{result['points_earned']} pts",
            "WRONG":   "✗  Not quite — see below",
        }
        self.score_result_lbl.config(
            text=grade_text[result["grade"]],
            fg=grade_colors[result["grade"]]
        )

        self.ideal_lbl.config(text=f'"{challenge["ideal_comment"]}"')
        self.explanation_lbl.config(text=challenge["explanation"])

        # Disable answer input and submit
        self.answer_box.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED, bg=DIM)

        # Show next button
        is_last = self.current_index >= SESSION_LENGTH - 1
        self.next_btn.config(
            text="VIEW RESULTS  →" if is_last else "NEXT CHALLENGE  →")
        self.next_btn.pack(anchor="w")

        # Update bottom bar
        self._update_bottom_bar()

        log_result(
            challenge_id   = challenge["id"],
            category       = challenge["category"],
            difficulty     = challenge["difficulty"],
            points_earned  = result["points_earned"],
            points_avail   = challenge["points"],
            grade          = result["grade"],
            user_answer    = user_answer
        )

    def _next_challenge(self):
        """
        Advances to the next challenge or ends the session.
        """
        self.current_index += 1
        if self.current_index >= SESSION_LENGTH:
            self._show_summary()
        else:
            self._load_challenge(self.session_challenges[self.current_index])

    def _update_bottom_bar(self):
        """
        Refreshes the score and accuracy labels after each submission.
        Accuracy is the percentage of challenges where the user scored
        at least partial credit — WRONG answers count as 0%.
        """
        self.score_lbl.config(text=f"Score: {self.session_score}")
        total    = len(self.session_results)
        credited = sum(
            1 for r in self.session_results if r["grade"] != "WRONG")
        acc = round(credited / total * 100) if total > 0 else 0
        self.accuracy_lbl.config(text=f"Accuracy: {acc}%")

    def _show_summary(self):
        """
        Replaces the challenge view with a session summary.
        Shows total score, accuracy, a breakdown by category,
        and a performance label based on the final score.
        """
        total_available = sum(r["points_avail"] for r in self.session_results)
        pct = round(self.session_score / total_available * 100) \
            if total_available > 0 else 0

        if pct >= 80:
            grade_text  = "Senior-Ready"
            grade_color = GREEN
        elif pct >= 55:
            grade_text  = "Mid-Level Awareness"
            grade_color = AMBER
        else:
            grade_text  = "Keep Reviewing"
            grade_color = RED

        for widget in self.root.winfo_children():
            widget.destroy()

        summary = tk.Frame(self.root, bg=REVIEW_BG)
        summary.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(summary, bg=REVIEW_BG)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            inner,
            text="ARI'Lab",
            font=("Consolas", 28, "bold"),
            bg=REVIEW_BG,
            fg=CODE_BG
        ).pack(pady=(0, 4))

        tk.Label(
            inner,
            text="Session Complete",
            font=("Arial", 13),
            bg=REVIEW_BG,
            fg=DIM
        ).pack(pady=(0, 32))

        tk.Label(
            inner,
            text=f"{self.session_score}  pts",
            font=("Arial", 48, "bold"),
            bg=REVIEW_BG,
            fg=CODE_BG
        ).pack()

        tk.Label(
            inner,
            text=f"out of {total_available} available",
            font=("Arial", 11),
            bg=REVIEW_BG,
            fg=DIM
        ).pack(pady=(0, 8))

        tk.Label(
            inner,
            text=grade_text,
            font=("Arial", 16, "bold"),
            bg=REVIEW_BG,
            fg=grade_color
        ).pack(pady=(0, 32))

        breakdown = tk.Frame(inner, bg=PANEL_BG)
        breakdown.pack(fill=tk.X, pady=(0, 24))

        category_totals = {}
        for r in self.session_results:
            cat = r["category"]
            if cat not in category_totals:
                category_totals[cat] = {"earned": 0, "avail": 0}
            category_totals[cat]["earned"] += r["points_earned"]
            category_totals[cat]["avail"]  += r["points_avail"]

        tk.Label(
            breakdown,
            text="BY CATEGORY",
            font=("Arial", 8, "bold"),
            bg=PANEL_BG,
            fg=DIM
        ).pack(anchor="w", padx=16, pady=(12, 4))

        for cat, totals in category_totals.items():
            icon = CATEGORY_ICONS.get(cat, "●")
            row  = tk.Frame(breakdown, bg=PANEL_BG)
            row.pack(fill=tk.X, padx=16, pady=2)
            tk.Label(
                row,
                text=f"{icon}  {cat}",
                font=("Arial", 9),
                bg=PANEL_BG,
                fg=REVIEW_FG,
                anchor="w"
            ).pack(side=tk.LEFT)
            cat_pct = round(
                totals["earned"] / totals["avail"] * 100) \
                if totals["avail"] > 0 else 0
            c = GREEN if cat_pct >= 70 else (AMBER if cat_pct >= 40 else RED)
            tk.Label(
                row,
                text=f"{totals['earned']}/{totals['avail']} pts  ({cat_pct}%)",
                font=("Arial", 9, "bold"),
                bg=PANEL_BG,
                fg=c
            ).pack(side=tk.RIGHT)

        tk.Label(breakdown, text="", bg=PANEL_BG).pack(pady=4)

        tk.Button(
            inner,
            text="NEW SESSION",
            font=("Arial", 11, "bold"),
            bg=BLUE,
            fg=WHITE,
            activebackground="#1A5CD4",
            activeforeground=WHITE,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=24,
            pady=12,
            command=self._restart
        ).pack()

    def _restart(self):
        """
        Destroys all widgets and rebuilds the full UI for a new session.
        Simpler than trying to reset every widget's state individually.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
        self.__init__(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    AriLabApp(root)
    root.mainloop()