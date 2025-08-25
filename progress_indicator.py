import os
import threading
import time

class ProgressIndicator:
    """Simple progress indicator for long-running operations."""

    def __init__(self):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.stop_spinner = False
        self.spinner_thread = None

    def _spin(self, message: str = "Processing"):
        """Spinner animation function."""
        idx = 0
        while not self.stop_spinner:
            print(f'\r{self.spinner_chars[idx % len(self.spinner_chars)]} {message}...', end='', flush=True)
            idx += 1
            time.sleep(0.1)
        print('\r' + ' ' * (len(message) + 10) + '\r', end='', flush=True)  # Clear the line

    def start(self, message: str = "Processing"):
        """Start the spinner."""
        self.stop_spinner = False
        self.spinner_thread = threading.Thread(target=self._spin, args=(message,))
        self.spinner_thread.daemon = True
        self.spinner_thread.start()

    def stop(self):
        """Stop the spinner."""
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join()