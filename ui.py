
import tkinter as tk
from tkinter import messagebox


class ClipFenceUI:

    def __init__(
        self,
        root,
        settings,
        on_settings,
        on_pause
    ):
        self.root = root
        self.settings = settings
        self.on_settings_changed = on_settings
        self.on_pause = on_pause

        self.root.title("ClipFence")
        self.root.geometry("620x740")
        self.root.resizable(False, False)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.hide_window
        )

        self._build()

    def _build(self):

        # Application title
        tk.Label(
            self.root,
            text="ClipFence",
            font=("Segoe UI", 24, "bold")
        ).pack(pady=(20, 5))

        tk.Label(
            self.root,
            text="Protect your clipboard before you paste.",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 20))

        # Protection toggle
        protection_frame = tk.Frame(self.root)
        protection_frame.pack(fill="x", padx=30)

        tk.Label(
            protection_frame,
            text="Protection",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        self.enabled_var = tk.BooleanVar(
            value=self.settings["enabled"]
        )

        tk.Checkbutton(
            protection_frame,
            text="ON",
            variable=self.enabled_var,
            command=self._toggle_enabled,
            font=("Segoe UI", 11)
        ).pack(side="right")

        # Activity status
        activity_frame = tk.Frame(
            self.root,
            bd=1,
            relief="solid",
            padx=12,
            pady=10
        )

        activity_frame.pack(
            fill="x",
            padx=30,
            pady=(15, 0)
        )

        tk.Label(
            activity_frame,
            text="Activity Status",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        self.protection_status_var = tk.StringVar(
            value="Protection is ON"
        )

        tk.Label(
            activity_frame,
            textvariable=self.protection_status_var,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))

        self.activity_var = tk.StringVar(
            value="Waiting for clipboard activity..."
        )

        tk.Label(
            activity_frame,
            textvariable=self.activity_var,
            font=("Segoe UI", 10),
            fg="#555555",
            wraplength=520,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

        # Separator
        tk.Frame(
            self.root,
            height=1,
            bg="#cccccc"
        ).pack(fill="x", padx=30, pady=20)

        # Detection settings
        tk.Label(
            self.root,
            text="Detection",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=30)

        self.detector_vars = {}

        detector_names = {
            "jwt": "JWT tokens",
            "api_keys": "API keys",
            "email": "Email addresses",
            "phone": "Phone numbers",
            "ipv4": "IPv4 addresses"
        }

        for key, label in detector_names.items():

            variable = tk.BooleanVar(
                value=self.settings["detectors"].get(key, False)
            )

            self.detector_vars[key] = variable

            tk.Checkbutton(
                self.root,
                text=label,
                variable=variable,
                command=self._detectors_changed,
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=45)

        # Custom sensitive words
        tk.Label(
            self.root,
            text="Custom sensitive words",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=30, pady=(20, 8))

        word_frame = tk.Frame(self.root)
        word_frame.pack(fill="x", padx=30)

        self.word_entry = tk.Entry(
            word_frame,
            font=("Segoe UI", 10)
        )

        self.word_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Button(
            word_frame,
            text="Add",
            command=self._add_word
        ).pack(side="right", padx=(10, 0))

        self.word_list = tk.Listbox(
            self.root,
            height=5,
            font=("Consolas", 10)
        )

        self.word_list.pack(
            fill="both",
            padx=30,
            pady=10
        )

        for word in self.settings["custom_words"]:
            self.word_list.insert(tk.END, word)

        tk.Button(
            self.root,
            text="Remove Selected",
            command=self._remove_word
        ).pack()

        # Replacement text
        tk.Label(
            self.root,
            text="Redaction replacement",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=30, pady=(20, 8))

        self.replacement_var = tk.StringVar(
            value=self.settings["replacement"]
        )

        tk.Entry(
            self.root,
            textvariable=self.replacement_var,
            font=("Segoe UI", 10)
        ).pack(fill="x", padx=30)

        tk.Button(
            self.root,
            text="Save Replacement",
            command=self._save_replacement
        ).pack(pady=8)

        # Pause protection
        tk.Button(
            self.root,
            text="Pause Protection (10 Minutes)",
            command=self.on_pause
        ).pack(pady=5)

        # Privacy information
        tk.Label(
            self.root,
            text="Local processing only • Clipboard contents are not stored.",
            font=("Segoe UI", 9)
        ).pack(pady=15)

    # Enable / disable protection
    def _toggle_enabled(self):
        self.settings["enabled"] = self.enabled_var.get()
        self._save()

        if self.enabled_var.get():
            self.set_protection_status("Protection is ON")
        else:
            self.set_protection_status("Protection is OFF")

    # Update detector settings
    def _detectors_changed(self):

        for key, variable in self.detector_vars.items():
            self.settings["detectors"][key] = variable.get()

        self._save()

    # Add custom word
    def _add_word(self):
        word = self.word_entry.get().strip()

        if not word:
            return

        existing_words = [
            item.lower()
            for item in self.settings["custom_words"]
        ]

        if word.lower() in existing_words:
            return

        self.settings["custom_words"].append(word)

        self.word_list.insert(tk.END, word)

        self.word_entry.delete(0, tk.END)

        self._save()

    # Remove selected custom word
    def _remove_word(self):
        selection = self.word_list.curselection()

        if not selection:
            return

        index = selection[0]

        self.word_list.delete(index)

        self.settings["custom_words"].pop(index)

        self._save()

    # Save replacement text
    def _save_replacement(self):
        replacement = self.replacement_var.get()

        if not replacement:
            messagebox.showwarning(
                "Invalid replacement",
                "Replacement cannot be empty."
            )
            return

        self.settings["replacement"] = replacement

        self._save()

    # Send updated settings to application
    def _save(self):
        self.on_settings_changed(self.settings)

    # Update protection status
    def set_protection_status(self, message):
        self.protection_status_var.set(message)

    # Update latest clipboard activity
    def set_activity(self, message):
        self.activity_var.set(message)

    # Display redaction result
    def show_redaction_notification(self, count):
        self.set_activity(
            f"{count} sensitive item(s) redacted."
        )

    # Show application window
    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    # Hide application window
    def hide_window(self):
        self.root.withdraw()
