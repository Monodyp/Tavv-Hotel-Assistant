# pyqt_tavv.py
import os
import sys
import sqlite3
import threading
from functools import partial

# optional: load .env (uncomment if using python-dotenv and a .env file)
from dotenv import load_dotenv
# load_dotenv()

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
)
from groq import Groq
from hotel_db import DatabaseLoader

# ---------------------------
# Load DB, tokens, and client
# ---------------------------
def read_device_token(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# create DB loader instance
db = DatabaseLoader()

device1_token = read_device_token("device1_token.txt")
device2_token = read_device_token("device2_token.txt")

info = None
if device2_token:
    info = db.get_resident_from_token(device2_token)

if not info:
    # Will be handled by the UI startup, but keep a fallback
    info = None

name = info["name"] if info and "name" in info else "Guest"
room = info["room_number"] if info and "room_number" in info else "000"

db_path = os.path.join("data", "hotel.db")
# ensure DB connection (may be used by db methods internally)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    # Let the UI show an error instead of crashing here.
    client = None
else:
    client = Groq(api_key=api_key)

# Conversation memory per room
conversation_history = {}

# ---------------------------
# Chat logic (adapted)
# ---------------------------
def build_system_prompt(current_day: str, room_number: str) -> dict:
    return {
        "role": "system",
        "content": (
            #Tavv Personality Injection
                "You are Tavv, a friendly but efficient hotel assistant. You are a conversational AI focused on engaging in authentic dialogue." "Today is " + current_day + ""
                #Retrival-Augmented Generation Prompt
                "Answer questions using the information in the provided database"
                #Limiting over-information and security breach
                "Only provide a response regarding to the user's specific prompt. Do not disclose any other information unless asked to. You're not allowed to compromise  the information of other rooms, for safety and privacy of the other residents. However, you can disclose information about the hotel's services like restaurant, accomodities, and amenities"
                #Room Identification
                "The guest is staying at room number" + room_number + ". Provide only the information in regards with their corresponding rooms." 
                #Response Limitation
                "When the user asks, try NOT to add instructions or steps unless the user explicitly requests: explain, how do I, or steps. Try not to overexplain or add unnecessary information."
                #Language accomodation
                "Speak in user's language. Switch the language based on user's input language."
                #IoT Feature
                "This hotel is equipped with IoT devices. You have full control over said IoT devices. That includes TV, Air-conditioning, and other IoT devices. If the user requests to control any device, only control the devices when user requests only. Do not include any technical details or code. Specify the changes made to the devices in your response clearly."
                #Miscellanaeous Instructions
                "When user implicates a sense of boredom, offer hotel activities from the activity center, or pools."
                "Any accomidty or service offered by the hotel (food, housekeeping,etc.) is included in the user's stay."
                "Detect the city the hotel's situated in, and recommend local attractions accordingly."
        ),
    }


def chat(user_input: str, room_number: str) -> str:
    """
    Synchronous chat call. This function performs network I/O (Groq).
    Run it in a background thread to avoid blocking the UI.
    """
    global client

    if client is None:
        return "ERROR: GROQ_API_KEY is not set. Put it in your environment."

    if room_number not in conversation_history:
        conversation_history[room_number] = []

    context_data = db.get_full_context(room_number)
    if not context_data:
        return "Sorry, could not find information for that room number."

    current_day = context_data.get("current_day", "today")
    context_text = str(context_data)

    system_msg = build_system_prompt(current_day, room_number)

    messages = [
        system_msg,
        {"role": "user", "content": f"Context:\n{context_text}\n\nUser question: {user_input}"},
    ]

    # add previous memory (if any)
    messages += conversation_history[room_number]

    # finally add the user's new message
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"ERROR: LLM request failed: {e}"

    # Save memory
    conversation_history[room_number].append({"role": "user", "content": user_input})
    conversation_history[room_number].append({"role": "assistant", "content": reply})

    return reply


# ---------------------------
# PyQt GUI
# ---------------------------
class Worker(QtCore.QObject):
    """Runs the chat() in a separate thread and emits the result."""
    finished = QtCore.pyqtSignal(str, str)  # (user_input, reply)
    started = QtCore.pyqtSignal()

    def __init__(self, user_input: str, room_number: str):
        super().__init__()
        self.user_input = user_input
        self.room_number = room_number

    @QtCore.pyqtSlot()
    def run(self):
        self.started.emit()
        reply = chat(self.user_input, self.room_number)
        self.finished.emit(self.user_input, reply)


class TavvWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tavv — Hotel Assistant")
        self.resize(640, 480)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Tavv</b> — Hello, {name} (room {room})")
        title.setTextFormat(QtCore.Qt.RichText)
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)

        # Conversation view (read-only)
        self.conv_view = QTextEdit()
        self.conv_view.setReadOnly(True)
        self.layout.addWidget(self.conv_view)

        # Input row
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.layout.addLayout(input_layout)

        # If client is not configured, show a big warning and disable input
        if client is None or info is None:
            self.show_startup_error()
        else:
            # greet in conversation view
            self.append_message("Tavv", f"Hello {name}. How can Tavv help you today?")

    def show_startup_error(self):
        self.append_message("System", "ERROR: Setup incomplete.")
        if client is None:
            self.append_message("System", "Missing GROQ_API_KEY environment variable.")
        if info is None:
            self.append_message("System", "Device token not found or not registered (device2_token.txt).")
        self.input_field.setDisabled(True)
        self.send_btn.setDisabled(True)

    def append_message(self, who: str, text: str):
        """Append a simple conversation line to the QTextEdit (plain, minimal formatting)."""
        self.conv_view.append(f"<b>{who}:</b> {text}\n")

    def on_send(self):
        text = self.input_field.text().strip()
        if not text:
            return

        # append user text locally immediately
        self.append_message("You", text)
        self.input_field.clear()
        self.send_btn.setDisabled(True)

        # start worker thread to call chat()
        worker = Worker(text, room)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        worker.started.connect(lambda: None)  # could disable UI actions if needed

        # when finished, update UI and clean up
        def handle_finished(user_input, reply):
            self.append_message("Tavv", reply)
            self.send_btn.setDisabled(False)
            # tidy up thread
            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()

        worker.finished.connect(handle_finished)
        thread.started.connect(worker.run)
        thread.start()


# ---------------------------
# Entry point
# ---------------------------
def main():
    app = QApplication(sys.argv)
    win = TavvWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
