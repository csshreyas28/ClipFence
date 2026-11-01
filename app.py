import threading
import time
import tkinter as tk

from settings import load_settings, save_settings
from redaction_engine import RedactionEngine
from clipboard_monitor import ClipboardMonitor
from tray import ClipFenceTray
from ui import ClipFenceUI


class ClipFenceApp:

    def __init__(self):
        self.settings = load_settings()

        self.pause_until = None
        self.pause_timer = None

        # Remember the previous protection state.
        # This lets us detect OFF -> ON transitions.
        self._last_enabled_state = bool(
            self.settings.get("enabled", False)
        )

        self.engine = RedactionEngine(
            self.settings
        )

        self.root = tk.Tk()

        self.ui = ClipFenceUI(
            self.root,
            self.settings,
            self.update_settings,
            self.pause_protection
        )

        self.monitor = ClipboardMonitor(
            self.is_enabled,
            self.process_clipboard,
            self.redaction_happened
        )

        self.tray = ClipFenceTray(
            self.show_window,
            self.toggle_protection,
            self.pause_protection,
            self.exit
        )

        self._refresh_ui()

    def start(self):
        print("Starting ClipFence...")

        self.monitor.start()

        print("Clipboard monitor started.")

        # If protection was already ON when ClipFence started,
        # process whatever is currently in the clipboard.
        if self.is_enabled():
            self.monitor.process_current_clipboard()

        tray_thread = threading.Thread(
            target=self.tray.run,
            daemon=True
        )

        tray_thread.start()

        self.root.mainloop()

    # Check whether protection is active
    def is_enabled(self):

        if not self.settings.get("enabled", False):
            return False

        if self.pause_until is not None:

            if time.time() < self.pause_until:
                return False

            self.pause_until = None

            self.root.after(
                0,
                self._refresh_ui
            )

        return True

    # Process clipboard content
    def process_clipboard(self, text):

        if not self.is_enabled():

            self.root.after(
                0,
                lambda: self.ui.set_activity(
                    "Protection is OFF or paused. Clipboard unchanged."
                )
            )

            return text, 0

        result, count = self.engine.redact(text)

        if count > 0:
            message = (
                f"{count} sensitive item(s) redacted."
            )
        else:
            message = (
                "No sensitive content detected."
            )

        self.root.after(
            0,
            lambda: self.ui.set_activity(message)
        )

        return result, count

    # Update settings from UI
    def update_settings(self, updated_settings):

        previous_enabled = self._last_enabled_state

        self.settings.update(
            updated_settings
        )

        save_settings(
            self.settings
        )

        self.engine.update_settings(
            self.settings
        )

        current_enabled = bool(
            self.settings.get("enabled", False)
        )

        self._last_enabled_state = current_enabled

        self.root.after(
            0,
            self._refresh_ui
        )

        # Protection has just changed from OFF -> ON.
        if current_enabled and not previous_enabled:

            # An active pause should not block an explicit re-enable.
            self.pause_until = None

            if self.pause_timer is not None:

                self.root.after_cancel(
                    self.pause_timer
                )

                self.pause_timer = None

            self.root.after(
                0,
                self._refresh_ui
            )

            self.monitor.process_current_clipboard()

    # Toggle protection from tray
    def toggle_protection(self):

        previous_enabled = bool(
            self.settings.get("enabled", False)
        )

        current_enabled = not previous_enabled

        self.settings["enabled"] = current_enabled

        save_settings(
            self.settings
        )

        self._last_enabled_state = current_enabled

        if current_enabled:

            # Explicitly enabling protection should resume protection.
            self.pause_until = None

            if self.pause_timer is not None:

                self.root.after_cancel(
                    self.pause_timer
                )

                self.pause_timer = None

            self.monitor.process_current_clipboard()

        self.root.after(
            0,
            self._refresh_ui
        )

    # Pause protection for 10 minutes
    def pause_protection(self):

        self.pause_until = time.time() + 600

        if self.pause_timer is not None:

            self.root.after_cancel(
                self.pause_timer
            )

        self.root.after(
            0,
            self._refresh_ui
        )

        self.pause_timer = self.root.after(
            600000,
            self._pause_finished
        )

    # Called when the 10-minute pause ends
    def _pause_finished(self):

        self.pause_timer = None

        if not self.settings.get("enabled", False):
            self.pause_until = None

            self._refresh_ui()
            return

        self.pause_until = None

        self._refresh_ui()

        # Protect whatever is currently in the clipboard.
        self.monitor.process_current_clipboard()

    # Called by clipboard monitor after redaction
    def redaction_happened(self, count):

        if count <= 0:
            return

        self.root.after(
            0,
            lambda: self.ui.show_redaction_notification(
                count
            )
        )

    # Show application window
    def show_window(self):

        self.root.after(
            0,
            self.ui.show_window
        )

    # Refresh UI status
    def _refresh_ui(self):

        self.ui.enabled_var.set(
            self.settings.get("enabled", False)
        )

        if not self.settings.get("enabled", False):

            self.ui.set_protection_status(
                "Protection is OFF"
            )

        elif (
            self.pause_until is not None
            and time.time() < self.pause_until
        ):

            self.ui.set_protection_status(
                "Protection is PAUSED"
            )

        else:

            self.pause_until = None

            self.ui.set_protection_status(
                "Protection is ON"
            )

    # Exit application
    def exit(self):

        self.monitor.stop()

        self.tray.stop()

        if self.pause_timer is not None:

            self.root.after_cancel(
                self.pause_timer
            )

        self.root.after(
            0,
            self.root.destroy
        )


if __name__ == "__main__":
    app = ClipFenceApp()
    app.start()