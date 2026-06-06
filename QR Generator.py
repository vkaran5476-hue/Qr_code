import qrcode
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import math, random, os, threading

# ══════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════
BG          = "#0a0a0f"
CARD        = "#12121a"
PANEL       = "#1a1a28"
ACCENT      = "#6c63ff"
ACCENT2     = "#ff6584"
ACCENT3     = "#43e97b"
TEXT        = "#e8e8f0"
MUTED       = "#5a5a7a"
BORDER      = "#2a2a40"
FONT_MONO   = "Courier New"
FONT_SANS   = "Segoe UI"

# ══════════════════════════════════════════════════════════
#  ROOT
# ══════════════════════════════════════════════════════════
root = tk.Tk()
root.title("QR Studio")
root.geometry("560x760")
root.resizable(False, False)
root.configure(bg=BG)

# ══════════════════════════════════════════════════════════
#  ANIMATED PARTICLE BACKGROUND
# ══════════════════════════════════════════════════════════
bg_canvas = tk.Canvas(root, width=560, height=760, bg=BG,
                      highlightthickness=0)
bg_canvas.place(x=0, y=0)

class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x  = random.randint(0, 560)
        self.y  = random.randint(0, 760)
        self.r  = random.uniform(1, 2.5)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, 0.3)
        colors  = [ACCENT, ACCENT2, ACCENT3, "#ffffff"]
        self.color = random.choice(colors)
        self.alpha = random.uniform(0.1, 0.4)
        # hex alpha approximation
        a = int(self.alpha * 255)
        self.draw_color = self.color + format(a, '02x')

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > 560 or self.y < 0 or self.y > 760:
            self.reset()

PARTICLES = [Particle() for _ in range(55)]

def animate_bg():
    bg_canvas.delete("particle")
    for p in PARTICLES:
        p.move()
        bg_canvas.create_oval(
            p.x - p.r, p.y - p.r, p.x + p.r, p.y + p.r,
            fill=p.color, outline="", tags="particle",
            stipple="gray25"
        )
    root.after(40, animate_bg)

# ══════════════════════════════════════════════════════════
#  HELPER WIDGETS
# ══════════════════════════════════════════════════════════
def lbl(parent, text, size=11, bold=False, fg=TEXT, bg=BG, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, font=(FONT_SANS, size, weight),
                    fg=fg, bg=bg, **kw)

class NeonEntry(tk.Frame):
    """Entry with animated underline accent."""
    def __init__(self, parent, textvariable=None, width=38, bg_frame=BG, **kw):
        super().__init__(parent, bg=PANEL, bd=0,
                         highlightthickness=1, highlightbackground=BORDER)
        self.configure(padx=0, pady=0)
        self.entry = tk.Entry(
            self, textvariable=textvariable, width=width,
            font=(FONT_SANS, 11), bg=PANEL, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            bd=0, highlightthickness=0
        )
        self.entry.pack(fill="x", ipady=8, padx=10)
        self.entry.bind("<FocusIn>",  lambda e: self.focus_in())
        self.entry.bind("<FocusOut>", lambda e: self.focus_out())

    def focus_in(self):
        self.configure(highlightbackground=ACCENT, highlightthickness=1)

    def focus_out(self):
        self.configure(highlightbackground=BORDER, highlightthickness=1)


class GlowButton(tk.Canvas):
    """Canvas-drawn button with hover glow animation."""
    def __init__(self, parent, text, command, width=160, height=42,
                 color=ACCENT, **kw):
        super().__init__(parent, width=width, height=height, bg=BG,
                         highlightthickness=0, cursor="hand2")
        self.command = command
        self.color   = color
        self.w, self.h = width, height
        self.text_str  = text
        self._glow = 0
        self._draw(False)
        self.bind("<Enter>",    lambda e: self._hover(True))
        self.bind("<Leave>",    lambda e: self._hover(False))
        self.bind("<Button-1>", lambda e: self._click())

    def _draw(self, hovered):
        self.delete("all")
        pad = 3
        r   = 8
        x0, y0, x1, y1 = pad, pad, self.w - pad, self.h - pad
        if hovered:
            # outer glow approximation (several rects)
            for i in range(4, 0, -1):
                self.create_rounded_rect(x0-i, y0-i, x1+i, y1+i,
                                         radius=r+i, fill="", outline=self.color,
                                         stipple="gray12", width=1)
        # filled button
        self.create_rounded_rect(x0, y0, x1, y1, radius=r,
                                 fill=self.color if hovered else PANEL,
                                 outline=self.color, width=1)
        fg = BG if hovered else self.color
        self.create_text(self.w//2, self.h//2,
                         text=self.text_str,
                         font=(FONT_SANS, 10, "bold"),
                         fill=fg)

    def create_rounded_rect(self, x0, y0, x1, y1, radius=8, **kw):
        points = [
            x0+radius, y0, x1-radius, y0,
            x1, y0, x1, y0+radius,
            x1, y1-radius, x1, y1,
            x1-radius, y1, x0+radius, y1,
            x0, y1, x0, y1-radius,
            x0, y0+radius, x0, y0,
        ]
        return self.create_polygon(points, smooth=True, **kw)

    def _hover(self, on):
        self._draw(on)

    def _click(self):
        self._draw(True)
        root.after(120, lambda: self._draw(False))
        if self.command:
            self.command()


class ColorSwatch(tk.Canvas):
    """Clickable colour swatch."""
    def __init__(self, parent, color, label, callback, size=36):
        super().__init__(parent, width=size+60, height=size+18,
                         bg=BG, highlightthickness=0, cursor="hand2")
        self.color    = color
        self.label    = label
        self.callback = callback
        self.size     = size
        self._redraw()
        self.bind("<Button-1>", lambda e: self._pick())

    def _redraw(self):
        self.delete("all")
        r = 6
        s = self.size
        # swatch rect
        self.create_rectangle(0, 9, s, 9+s, fill=self.color,
                               outline=BORDER, width=1)
        # label
        self.create_text(s+8, 9+s//2, text=self.label,
                         anchor="w", font=(FONT_SANS, 9), fill=MUTED)

    def _pick(self):
        result = colorchooser.askcolor(color=self.color,
                                        title=f"Pick {self.label}")
        if result and result[1]:
            self.color = result[1]
            self._redraw()
            self.callback(result[1])

    def get(self):
        return self.color


class SpinField(tk.Frame):
    """Compact labelled spinbox."""
    def __init__(self, parent, label, from_, to, default, bg=BG):
        super().__init__(parent, bg=bg)
        tk.Label(self, text=label, font=(FONT_SANS, 9), fg=MUTED,
                 bg=bg).pack(anchor="w")
        self.var = tk.IntVar(value=default)
        frame = tk.Frame(self, bg=PANEL, highlightthickness=1,
                         highlightbackground=BORDER)
        frame.pack(anchor="w")
        tk.Spinbox(frame, from_=from_, to=to, textvariable=self.var,
                   width=4, font=(FONT_SANS, 11), bg=PANEL, fg=TEXT,
                   buttonbackground=PANEL, relief="flat",
                   highlightthickness=0, insertbackground=ACCENT
                   ).pack(ipady=5, padx=4)

    def get(self):
        return self.var.get()


# ══════════════════════════════════════════════════════════
#  LAYOUT — all elements placed over bg_canvas
# ══════════════════════════════════════════════════════════
MAIN = tk.Frame(root, bg=BG)
MAIN.place(x=0, y=0, width=560, height=760)

# ── Header ────────────────────────────────────────────────
header = tk.Frame(MAIN, bg=BG)
header.pack(fill="x", padx=28, pady=(22, 4))

title_f = tk.Frame(header, bg=BG)
title_f.pack(side="left")

tk.Label(title_f, text="QR", font=(FONT_MONO, 28, "bold"),
         fg=ACCENT, bg=BG).pack(side="left")
tk.Label(title_f, text=" STUDIO", font=(FONT_MONO, 28, "bold"),
         fg=TEXT, bg=BG).pack(side="left")

tk.Label(header, text="v2.0", font=(FONT_SANS, 9),
         fg=MUTED, bg=BG).pack(side="right", anchor="s", pady=6)

# animated accent line
accent_canvas = tk.Canvas(MAIN, height=2, bg=BG, highlightthickness=0)
accent_canvas.pack(fill="x", padx=28)
_line_pos = [0]

def animate_line():
    accent_canvas.delete("all")
    w = accent_canvas.winfo_width() or 504
    pos = _line_pos[0]
    # gradient-like moving highlight
    for i in range(w):
        t = (i - pos) % w
        if t < 120:
            brightness = int(255 * math.sin(math.pi * t / 120))
            col = "#{:02x}{:02x}{:02x}".format(
                int(0x6c + (0xff - 0x6c) * brightness // 255),
                int(0x63 + (0xff - 0x63) * brightness // 255),
                0xff)
            accent_canvas.create_line(i, 0, i, 2, fill=col)
        else:
            accent_canvas.create_line(i, 0, i, 2, fill=BORDER)
    _line_pos[0] = (pos + 2) % w
    root.after(30, animate_line)

# ── Input card ────────────────────────────────────────────
input_card = tk.Frame(MAIN, bg=CARD, bd=0,
                      highlightthickness=1, highlightbackground=BORDER)
input_card.pack(fill="x", padx=28, pady=(14, 0))

tk.Label(input_card, text="  URL / TEXT", font=(FONT_SANS, 9, "bold"),
         fg=ACCENT, bg=PANEL).pack(fill="x", ipady=5)

url_var = tk.StringVar(value="https://www.google.com")
url_entry_frame = tk.Frame(input_card, bg=CARD)
url_entry_frame.pack(fill="x", padx=14, pady=10)

url_entry = NeonEntry(url_entry_frame, textvariable=url_var, width=50, bg_frame=CARD)
url_entry.pack(fill="x")

# ── Options row ───────────────────────────────────────────
opts_card = tk.Frame(MAIN, bg=CARD, bd=0,
                     highlightthickness=1, highlightbackground=BORDER)
opts_card.pack(fill="x", padx=28, pady=(8, 0))

tk.Label(opts_card, text="  OPTIONS", font=(FONT_SANS, 9, "bold"),
         fg=ACCENT, bg=PANEL).pack(fill="x", ipady=5)

opts_row = tk.Frame(opts_card, bg=CARD)
opts_row.pack(fill="x", padx=14, pady=10)

box_spin    = SpinField(opts_row, "BOX SIZE",  5, 20,  10, bg=CARD)
border_spin = SpinField(opts_row, "BORDER",    1, 10,   4, bg=CARD)

# error correction
err_frm = tk.Frame(opts_row, bg=CARD)
tk.Label(err_frm, text="ERROR CORR.",
         font=(FONT_SANS, 9), fg=MUTED, bg=CARD).pack(anchor="w")
err_var = tk.StringVar(value="H")
err_inner = tk.Frame(err_frm, bg=PANEL, highlightthickness=1,
                     highlightbackground=BORDER)
err_inner.pack(anchor="w")
for val in ["L", "M", "Q", "H"]:
    tk.Radiobutton(
        err_inner, text=val, variable=err_var, value=val,
        font=(FONT_SANS, 10), bg=PANEL, fg=TEXT,
        selectcolor=ACCENT, activebackground=PANEL,
        indicatoron=0, relief="flat", width=3,
        cursor="hand2", pady=4
    ).pack(side="left", padx=2)

for w in [box_spin, border_spin, err_frm]:
    w.pack(side="left", padx=(0, 20))

# ── Colours ───────────────────────────────────────────────
col_card = tk.Frame(MAIN, bg=CARD, bd=0,
                    highlightthickness=1, highlightbackground=BORDER)
col_card.pack(fill="x", padx=28, pady=(8, 0))

tk.Label(col_card, text="  COLOURS", font=(FONT_SANS, 9, "bold"),
         fg=ACCENT, bg=PANEL).pack(fill="x", ipady=5)

col_row = tk.Frame(col_card, bg=CARD)
col_row.pack(fill="x", padx=14, pady=10)

fill_color_val = ["#000000"]
back_color_val = ["#ffffff"]

fill_swatch = ColorSwatch(col_row, "#000000", "QR colour",
                          lambda c: fill_color_val.__setitem__(0, c))
fill_swatch.pack(side="left", padx=(0, 20))

back_swatch = ColorSwatch(col_row, "#ffffff", "Background",
                          lambda c: back_color_val.__setitem__(0, c))
back_swatch.pack(side="left")

# ── Generate button ───────────────────────────────────────
btn_row = tk.Frame(MAIN, bg=BG)
btn_row.pack(pady=14)

current_pil = [None]

def do_generate():
    data = url_var.get().strip()
    if not data:
        messagebox.showwarning("Empty", "Please enter a URL or text.")
        return

    err_map = {"L": qrcode.constants.ERROR_CORRECT_L,
               "M": qrcode.constants.ERROR_CORRECT_M,
               "Q": qrcode.constants.ERROR_CORRECT_Q,
               "H": qrcode.constants.ERROR_CORRECT_H}

    status_var.set("⟳  generating…")
    gen_btn.configure(state="disabled")
    root.update_idletasks()

    def _gen():
        try:
            qr_obj = qrcode.QRCode(
                version=1,
                error_correction=err_map[err_var.get()],
                box_size=box_spin.get(),
                border=border_spin.get()
            )
            qr_obj.add_data(data)
            qr_obj.make(fit=True)
            img = qr_obj.make_image(
                fill_color=fill_swatch.get(),
                back_color=back_swatch.get()
            )
            current_pil[0] = img
            root.after(0, _update_preview, img)
        except Exception as ex:
            root.after(0, lambda: messagebox.showerror("Error", str(ex)))
        finally:
            root.after(0, lambda: gen_btn.configure(state="normal"))

    threading.Thread(target=_gen, daemon=True).start()

gen_btn = GlowButton(btn_row, "✦  GENERATE QR CODE  ✦",
                     do_generate, width=260, height=46, color=ACCENT)
gen_btn.pack(side="left", padx=8)

save_btn = GlowButton(btn_row, "↓  SAVE",
                      lambda: save_image(), width=110, height=46, color=ACCENT3)
save_btn.pack(side="left")

# ── Preview ───────────────────────────────────────────────
preview_outer = tk.Frame(MAIN, bg=CARD, bd=0,
                         highlightthickness=1, highlightbackground=BORDER)
preview_outer.pack(padx=28, pady=(0, 8))

preview_canvas = tk.Canvas(preview_outer, width=504, height=280,
                            bg=CARD, highlightthickness=0)
preview_canvas.pack()

_tk_img     = [None]
_ring_angle = [0]
_pulse      = [0.0]
_pulse_dir  = [1]
_is_ready   = [False]

def draw_idle():
    preview_canvas.delete("all")
    cx, cy = 252, 140
    # dashed circle
    r = 80
    for i in range(36):
        a1 = math.radians(i * 10 + _ring_angle[0])
        a2 = math.radians(i * 10 + 7 + _ring_angle[0])
        x1 = cx + r * math.cos(a1)
        y1 = cy + r * math.sin(a1)
        x2 = cx + r * math.cos(a2)
        y2 = cy + r * math.sin(a2)
        preview_canvas.create_line(x1, y1, x2, y2, fill=ACCENT,
                                   width=2, capstyle="round")
    # inner text
    preview_canvas.create_text(cx, cy-10, text="◈",
                                font=(FONT_MONO, 22), fill=ACCENT)
    preview_canvas.create_text(cx, cy+18, text="awaiting input",
                                font=(FONT_SANS, 9), fill=MUTED)
    _ring_angle[0] = (_ring_angle[0] + 1.5) % 360

def draw_ready(tk_img):
    preview_canvas.delete("all")
    # pulsing border
    _pulse[0] += 0.05 * _pulse_dir[0]
    if _pulse[0] >= 1.0: _pulse_dir[0] = -1
    if _pulse[0] <= 0.0: _pulse_dir[0] =  1
    brightness = int(80 + 100 * _pulse[0])
    border_col = "#{:02x}{:02x}ff".format(brightness, brightness)
    pad = 6
    preview_canvas.create_rectangle(
        pad, pad, 504-pad, 280-pad,
        outline=border_col, width=1, dash=(4, 4)
    )
    # image
    preview_canvas.create_image(252, 140, image=tk_img)

def _animate_preview():
    if _is_ready[0]:
        draw_ready(_tk_img[0])
    else:
        draw_idle()
    root.after(30, _animate_preview)

def _update_preview(pil_img):
    size = 240
    disp = pil_img.resize((size, size), Image.NEAREST)
    _tk_img[0] = ImageTk.PhotoImage(disp)
    _is_ready[0] = True
    status_var.set("✓  ready  —  click SAVE to export")

# ── Status bar ────────────────────────────────────────────
status_bar = tk.Frame(MAIN, bg=PANEL, height=28)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

status_var = tk.StringVar(value="↑  enter a URL above and hit GENERATE")
tk.Label(status_bar, textvariable=status_var,
         font=(FONT_SANS, 9), fg=MUTED, bg=PANEL,
         anchor="w").pack(side="left", padx=14, fill="y")

# version tag
tk.Label(status_bar, text="made with qrcode + PIL",
         font=(FONT_SANS, 8), fg=BORDER, bg=PANEL).pack(side="right", padx=10)

# ══════════════════════════════════════════════════════════
#  SAVE
# ══════════════════════════════════════════════════════════
def save_image():
    if current_pil[0] is None:
        messagebox.showinfo("Nothing to save", "Generate a QR code first!")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All files", "*.*")],
        initialfile="qrcode"
    )
    if path:
        current_pil[0].save(path)
        status_var.set(f"✓  saved → {os.path.basename(path)}")

# ══════════════════════════════════════════════════════════
#  KICK OFF ANIMATIONS
# ══════════════════════════════════════════════════════════
root.after(200, animate_bg)
root.after(300, animate_line)
root.after(400, _animate_preview)

root.mainloop()