import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from exporter import export_csv
from scraper import scrape, start_driver, login, get_tahun_list, get_prodi_list


# =============================
# PERSONA 3 RELOAD INSPIRED UI
# =============================
BG = "#07111f"
PANEL = "#0c1d33"
PANEL_ALT = "#102845"
ACCENT = "#38c8ff"
ACCENT_2 = "#8ee7ff"
TEXT = "#f2f8ff"
MUTED = "#9db6d4"
SUCCESS = "#64f0b0"
WARNING = "#ffd166"
DANGER = "#ff7b8a"
BORDER = "#1f4f7b"

APP_TITLE = "UBP E-Learning Scraper"
OUTPUT_FILE = os.path.join("data", "hasil_scraping.csv")


def safe_open_output_folder():
    folder = os.path.abspath("data")
    os.makedirs(folder, exist_ok=True)
    try:
        os.startfile(folder)
    except Exception:
        messagebox.showinfo("Info", f"Folder output ada di:\n{folder}")


class ScraperUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x680")
        self.root.minsize(860, 600)
        self.root.configure(bg=BG)

        self.tahun_data = []
        self.prodi_data = []

        self.last_selected_tahun = None
        self.loading_prodi = False
        self.is_running = False

        # ======================
        # VARIABLE
        # ======================
        self.tahun_var = tk.StringVar(value="TAHUN AKADEMIK 2025/2026")
        self.prodi_var = tk.StringVar(value="Teknik Informatika")
        self.status_var = tk.StringVar(value="READY")
        self.output_var = tk.StringVar(value=os.path.abspath(OUTPUT_FILE))

        # ======================
        # INIT UI
        # ======================
        self._setup_style()
        self._build_layout()

        # ======================
        # DEFAULT DROPDOWN DATA (NO SELENIUM)
        # ======================
        self.tahun_dropdown["values"] = [
            "TAHUN AKADEMIK 2025/2026",
            "TAHUN AKADEMIK 2024/2025",
        ]

        self.prodi_dropdown["values"] = [
            "Teknik Informatika",
            "Sistem Informasi",
            "Psikologi",
            "Teknik Industri",
            "Teknik Mesin",
            "Manajemen",
            "Akuntansi",
            "Ilmu Hukum",
            "Farmasi",
            "Pendidikan Agama Islam",
            "Pendidikan Pancasila dan Kewarganegaraan",
            "Pendidikan Guru Sekolah Dasar",
            "Manajemen S2",
            "Pendidikan Profesi Guru",
        ]

        # ======================
        # LOG
        # ======================
        self._append_log("Sistem siap. Pilih Tahun Akademik dan Prodi lalu tekan START.")
        self._append_log("Tema dibuat dengan nuansa biru terang ala Persona 3 Reload.")

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = ("Segoe UI", 10)
        title_font = ("Segoe UI Semibold", 24)
        section_font = ("Segoe UI Semibold", 11)

        self.root.option_add("*Font", default_font)

        style.configure("Main.TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL, relief="flat")
        style.configure("AltCard.TFrame", background=PANEL_ALT, relief="flat")
        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=title_font,
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=ACCENT_2,
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=PANEL,
            foreground=ACCENT_2,
            font=section_font,
        )
        style.configure(
            "Body.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=PANEL,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=PANEL_ALT,
            foreground=TEXT,
            font=("Consolas", 11, "bold"),
        )
        style.configure(
            "TSeparator",
            background=BORDER,
        )

        style.configure(
            "P3.TButton",
            background=ACCENT,
            foreground="#031522",
            borderwidth=0,
            focusthickness=0,
            focuscolor=ACCENT,
            font=("Segoe UI Semibold", 10),
            padding=(18, 12),
        )
        style.map(
            "P3.TButton",
            background=[("active", ACCENT_2), ("disabled", "#29506a")],
            foreground=[("disabled", "#d7ebf3")],
        )

        style.configure(
            "Ghost.TButton",
            background=PANEL_ALT,
            foreground=TEXT,
            borderwidth=0,
            focusthickness=0,
            focuscolor=PANEL_ALT,
            font=("Segoe UI Semibold", 10),
            padding=(14, 10),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#173861"), ("disabled", "#193047")],
            foreground=[("disabled", "#7c97b5")],
        )

        style.configure(
            "P3.TCombobox",
            fieldbackground="#0b1a2d",
            background="#0b1a2d",
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            arrowcolor=ACCENT_2,
            padding=8,
        )
        style.map(
            "P3.TCombobox",
            fieldbackground=[("readonly", "#0b1a2d")],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", "#16385e")],
            selectforeground=[("readonly", TEXT)],
        )

        style.configure(
            "P3.Horizontal.TProgressbar",
            troughcolor="#0b1a2d",
            background=ACCENT,
            bordercolor="#0b1a2d",
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )

    def _build_layout(self):
        container = ttk.Frame(self.root, style="Main.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(1, weight=1)

        self._build_header(container)
        self._build_left_panel(container)
        self._build_right_panel(container)

    def _build_header(self, parent):
        header = ttk.Frame(parent, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Stylized dark-blue dashboard · inspired by Persona 3 Reload",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        badge = tk.Label(
            header,
            textvariable=self.status_var,
            bg=PANEL_ALT,
            fg=ACCENT_2,
            padx=16,
            pady=8,
            font=("Consolas", 11, "bold"),
            relief="flat",
            bd=0,
        )
        badge.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_left_panel(self, parent):
        left = ttk.Frame(parent, style="Card.TFrame", padding=18)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(6, weight=1)

        ttk.Label(left, text="Control Panel", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            left,
            text="Pilih target scraping lalu jalankan proses. Hasil akan otomatis disimpan ke CSV.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        form = tk.Frame(left, bg=PANEL)
        form.grid(row=2, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self._create_field(
            form,
            row=0,
            col=0,
            label="Tahun Akademik",
            values=[],
            variable=self.tahun_var,
        )
        self._create_field(
            form,
            row=0,
            col=1,
            label="Program Studi",
            values=[],
            variable=self.prodi_var,
        )

        button_row = ttk.Frame(left, style="Card.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(16, 12))
        button_row.columnconfigure((0, 1, 2), weight=1)

        self.start_button = ttk.Button(
            button_row,
            text="START SCRAPING",
            style="P3.TButton",
            command=self.start_scraping,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(
            button_row,
            text="CLEAR LOG",
            style="Ghost.TButton",
            command=self.clear_log,
        ).grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Button(
            button_row,
            text="OPEN OUTPUT",
            style="Ghost.TButton",
            command=safe_open_output_folder,
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.progress = ttk.Progressbar(
            left,
            mode="indeterminate",
            style="P3.Horizontal.TProgressbar",
        )
        self.progress.grid(row=4, column=0, sticky="ew", pady=(4, 14))

        info = ttk.Frame(left, style="AltCard.TFrame", padding=14)
        info.grid(row=5, column=0, sticky="ew", pady=(0, 14))
        info.columnconfigure(1, weight=1)

        self._info_row(info, 0, "Status", self.status_var)
        self._info_row(info, 1, "Output", self.output_var)

        log_wrap = ttk.Frame(left, style="Card.TFrame")
        log_wrap.grid(row=6, column=0, sticky="nsew")
        log_wrap.columnconfigure(0, weight=1)
        log_wrap.rowconfigure(1, weight=1)

        ttk.Label(log_wrap, text="Activity Log", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.log_text = ScrolledText(
            log_wrap,
            wrap="word",
            height=16,
            bg="#081525",
            fg=ACCENT_2,
            insertbackground=ACCENT_2,
            relief="flat",
            bd=0,
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

    def _build_right_panel(self, parent):
        right = ttk.Frame(parent, style="AltCard.TFrame", padding=18)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Visual Notes", style="Status.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        title = tk.Label(
            right,
            text="SEES-STYLE TERMINAL",
            bg=PANEL_ALT,
            fg=ACCENT,
            font=("Segoe UI Semibold", 18),
            anchor="w",
        )
        title.grid(row=1, column=0, sticky="ew", pady=(10, 8))

        block = tk.Frame(right, bg="#0a1b31", highlightbackground=BORDER, highlightthickness=1)
        block.grid(row=2, column=0, sticky="nsew", pady=(4, 12))
        block.grid_columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        sections = [
            ("01", "Clean dashboard", "Tampilan dibuat lebih tajam, gelap, dan bercahaya biru."),
            ("02", "Safer threading", "Update UI dilakukan aman dari thread background."),
            ("03", "One-click run", "Tinggal buka batch file lalu aplikasi siap dipakai."),
            ("04", "CSV export", "Hasil otomatis disimpan ke folder data setelah scraping selesai."),
        ]

        for idx, (code, heading, desc) in enumerate(sections):
            card = tk.Frame(block, bg="#0a1b31")
            card.grid(row=idx, column=0, sticky="ew", padx=14, pady=10)
            card.grid_columnconfigure(1, weight=1)

            num = tk.Label(
                card,
                text=code,
                bg=ACCENT,
                fg="#031522",
                width=4,
                pady=8,
                font=("Consolas", 11, "bold"),
            )
            num.grid(row=0, column=0, rowspan=2, sticky="n")

            tk.Label(
                card,
                text=heading.upper(),
                bg="#0a1b31",
                fg=TEXT,
                anchor="w",
                font=("Segoe UI Semibold", 11),
            ).grid(row=0, column=1, sticky="w", padx=(12, 0))
            tk.Label(
                card,
                text=desc,
                bg="#0a1b31",
                fg=MUTED,
                justify="left",
                wraplength=260,
                anchor="w",
                font=("Segoe UI", 9),
            ).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(3, 0))

        footer = tk.Label(
            right,
            text="Tip: pastikan file .env sudah berisi MOODLE_USERNAME dan MOODLE_PASSWORD.",
            bg=PANEL_ALT,
            fg=WARNING,
            justify="left",
            wraplength=320,
            anchor="w",
            font=("Segoe UI", 9),
        )
        footer.grid(row=3, column=0, sticky="ew", pady=(8, 0))

    def _create_field(self, parent, row, col, label, values, variable):
        frame = tk.Frame(parent, bg=PANEL)
        frame.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0 if col == 0 else 8, 8 if col == 0 else 0),
            pady=(0, 8)
        )
        frame.grid_columnconfigure(0, weight=1)

        # ======================
        # LABEL
        # ======================
        tk.Label(
            frame,
            text=label,
            bg=PANEL,
            fg=TEXT,
            anchor="w",
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        # ======================
        # COMBOBOX
        # ======================
        combo = ttk.Combobox(
            frame,
            textvariable=variable,
            values=values,
            state="readonly",
            style="P3.TCombobox",
        )
        combo.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # ======================
        # ASSIGN DROPDOWN + EVENT
        # ======================
        if label == "Tahun Akademik":
            self.tahun_dropdown = combo

            # bind hanya sekali, aman dari loop
            # combo.bind("<<ComboboxSelected>>", self._on_tahun_changed)

        elif label == "Program Studi":
            self.prodi_dropdown = combo

        return combo



    def _info_row(self, parent, row, label, variable):
        tk.Label(
            parent,
            text=f"{label}",
            bg=PANEL_ALT,
            fg=ACCENT_2,
            anchor="w",
            font=("Segoe UI Semibold", 10),
        ).grid(row=row, column=0, sticky="nw", pady=4)

        tk.Label(
            parent,
            textvariable=variable,
            bg=PANEL_ALT,
            fg=TEXT,
            anchor="w",
            justify="left",
            wraplength=430,
            font=("Segoe UI", 9),
        ).grid(row=row, column=1, sticky="nw", padx=(12, 0), pady=4)

    def _set_running(self, running: bool):
        self.is_running = running
        if running:
            self.status_var.set("SCRAPING...")
            self.start_button.state(["disabled"])
            self.progress.start(10)
        else:
            self.status_var.set("READY")
            self.start_button.state(["!disabled"])
            self.progress.stop()

    def _append_log(self, message: str):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self._append_log("Log dibersihkan.")

    def start_scraping(self):
        if self.is_running:
            return

        tahun = self.tahun_var.get().strip()
        prodi = self.prodi_var.get().strip()

        if not tahun or not prodi:
            messagebox.showwarning("Warning", "Isi Tahun dan Prodi dulu!")
            return

        self._set_running(True)
        self._append_log("=" * 60)
        self._append_log(f"Mulai scraping: {tahun} | {prodi}")
        self._append_log("Memulai browser...")

        def run_job():
            try:
                # ======================
                # START DRIVER SEKALI SAJA
                # ======================
                driver, wait = start_driver()
                login(driver, wait)

                # ======================
                # AMBIL TAHUN
                # ======================
                self.root.after(0, lambda: self._append_log("Mengambil data tahun..."))
                tahun_list = get_tahun_list(driver, wait)

                tahun_obj = next(
                    (t for t in tahun_list if tahun.lower() in t["nama"].lower()),
                    None
                )

                if not tahun_obj:
                    raise Exception("Tahun tidak ditemukan")

                # ======================
                # AMBIL PRODI
                # ======================
                self.root.after(0, lambda: self._append_log("Mengambil data prodi..."))
                prodi_list = get_prodi_list(driver, wait, tahun_obj["url"])

                prodi_obj = next(
                    (p for p in prodi_list if prodi.lower() in p["nama"].lower()),
                    None
                )

                if not prodi_obj:
                    raise Exception("Prodi tidak ditemukan")

                # ======================
                # SCRAPING UTAMA
                # ======================
                data = scrape(tahun_obj, prodi_obj, driver, wait)

                export_csv(data, OUTPUT_FILE)

                driver.quit()

                # ======================
                # SUCCESS
                # ======================
                self.root.after(0, lambda: self._append_log(f"Selesai. Total data: {len(data)}"))

                self.root.after(0, lambda: messagebox.showinfo(
                    "Sukses",
                    f"Data berhasil disimpan\n{os.path.abspath(OUTPUT_FILE)}"
                ))

            except Exception as e:
                self.root.after(0, lambda e=e: self._handle_error(e))

            finally:
                self.is_running = False
                self.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=run_job, daemon=True).start()

    
    # handle error

    def _handle_error(self, e):
        self._append_log(f"Error: {e}")
        self._set_running(False)
        messagebox.showerror("Error", str(e))


def run_app():
    root = tk.Tk()
    ScraperUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
