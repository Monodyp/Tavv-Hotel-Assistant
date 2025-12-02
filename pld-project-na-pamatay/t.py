from setup_env import setup_venv
setup_venv()

import os
import sys
from groq import Groq
import sqlite3
from hotel_db import DatabaseLoader
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QScrollArea, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QColor
import cv2
import numpy as np

# Initialize database and API
db = DatabaseLoader()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
conversation_history = {}

# Read device token
def read_device_token(file_path):
    with open(file_path, "r") as f:
        return f.read().strip()

device_token = read_device_token("device1_token.txt")
info = db.get_resident_from_token(device_token)

if not info:
    print("ERROR: Your device token is not registered in the hotel system.")
    exit()

name = info["name"]
room = info["room_number"]

# Extract first name only
first_name = name.split()[0] if name else name

# Chat function (same as original)
def chat(user_input, room_number):
    if room_number not in conversation_history:
        conversation_history[room_number] = []

    context_data = db.get_full_context(room_number)
    
    if not context_data:
        return "Sorry, I couldn't find information for that room. Please check your room number."

    current_day = context_data.get('current_day', 'today')
    context_text = str(context_data)

    conversation = {
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
                "If, and ONLY IF, user asks for price of any accomidty or service offered by the hotel (food, housekeeping,etc.), it is included in the user's stay."
                "Detect the city the hotel's situated in, and recommend local attractions accordingly."
        )
    }

    messages = [conversation, {"role": "user", "content": f"Context:\n{context_text}\n\nUser question: {user_input}"}]
    messages += conversation_history[room_number]
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages  
    )

    reply = response.choices[0].message.content

    conversation_history[room_number].append({"role": "user", "content": user_input})
    conversation_history[room_number].append({"role": "assistant", "content": reply})

    return reply

# Worker thread for API calls
class ChatWorker(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, user_input, room_number):
        super().__init__()
        self.user_input = user_input
        self.room_number = room_number
    
    def run(self):
        response = chat(self.user_input, self.room_number)
        self.finished.emit(response)

# Main GUI
class TavvGUI(QMainWindow):
    def __init__(self, guest_name, room_number, video_path="background.mp4"):
        super().__init__()
        self.guest_name = guest_name
        self.room_number = room_number
        self.video_path = video_path
        self.first_message = None
        self.chat_state = False
        
        self.setWindowTitle("Tavv - Canyon Cove Hotel")
        self.setFixedSize(640, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Video background label
        self.video_label = QLabel(central_widget)
        self.video_label.setGeometry(0, 0, 640, 800)
        self.video_label.setScaledContents(False)  # Don't scale, let it crop naturally
        self.video_label.setAlignment(Qt.AlignCenter)
        
        # Dark overlay on top of video
        self.overlay = QLabel(central_widget)
        self.overlay.setGeometry(0, 0, 640, 800)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 110);")
        
        # Load video with OpenCV
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
        
        if not os.path.exists(video_path):
            print(f"WARNING: Video file not found at: {video_path}")
            print("The app will run with a dark background.")
            self.video_label.setStyleSheet("background-color: #0a1628;")
            self.cap = None
        else:
            print(f"Loading video from: {video_path}")
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print("ERROR: Could not open video file")
                self.video_label.setStyleSheet("background-color: #0a1628;")
                self.cap = None
            else:
                self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
                if self.video_fps == 0:
                    self.video_fps = 30
                self.frame_delay = int(1000 / self.video_fps)
                print(f"Video loaded successfully. FPS: {self.video_fps}")
                
                # Start video playback
                self.video_timer = QTimer()
                self.video_timer.timeout.connect(self.update_video_frame)
                self.video_timer.start(self.frame_delay)
        
        # Main container with margins
        self.main_widget = QWidget(central_widget)
        self.main_widget.setGeometry(30, 30, 580, 740)  # 30px margins on all sides
        self.main_widget.setStyleSheet("background: transparent;")
        
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding
        self.main_layout.setSpacing(0)
        
        # Welcome screen
        self.welcome_container = QWidget()
        self.welcome_container.setStyleSheet("background: transparent;")
        self.welcome_container.setMaximumWidth(500)  # Constrain width to fit within margins
        welcome_layout = QVBoxLayout(self.welcome_container)
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(20)
        
        self.welcome_label = QLabel(f"Hello, {self.guest_name}")
        self.welcome_label.setFont(QFont("Inter", 28, QFont.Bold))
        self.welcome_label.setStyleSheet("color: white; background: transparent;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setGraphicsEffect(self.create_shadow())
        welcome_layout.addWidget(self.welcome_label)
        
        self.subtitle_label = QLabel("How can I help you?")
        self.subtitle_label.setFont(QFont("Inter", 14))
        self.subtitle_label.setStyleSheet("color: white; background: transparent;")  # Changed to white
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setGraphicsEffect(self.create_shadow())
        welcome_layout.addWidget(self.subtitle_label)
        
        # Startup input
        input_container = QWidget()
        input_container.setFixedWidth(400)
        input_container.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 20, 0, 0)
        
        self.startup_input = QLineEdit()
        self.startup_input.setFont(QFont("Inter", 12))
        self.startup_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(26, 43, 71, 150);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
            }
        """)
        self.startup_input.setPlaceholderText("Ask Something...")
        self.startup_input.returnPressed.connect(self.first_message_send)
        input_layout.addWidget(self.startup_input)
        
        self.startup_button = QPushButton("→")
        self.startup_button.setFont(QFont("Inter", 16, QFont.Bold))
        self.startup_button.setFixedSize(50, 45)
        self.startup_button.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
        """)
        self.startup_button.clicked.connect(self.first_message_send)
        input_layout.addWidget(self.startup_button)
        
        welcome_layout.addWidget(input_container, alignment=Qt.AlignCenter)
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.welcome_container, alignment=Qt.AlignCenter)
        self.main_layout.addStretch()
        
        # Logo in top left corner
        self.logo_label = QLabel(central_widget)  # Position relative to central_widget, not main_widget
        logo_path = r"C:\Users\Ocnarf\Tavv-Hotel-Assistant\pld-project-na-pamatay\media\logo.png"  # Change this to your logo file path
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Scale logo to reasonable size (e.g., 100px wide, maintain aspect ratio)
            logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback text if logo not found
            self.logo_label.setText("TAVV")
            self.logo_label.setFont(QFont("Inter", 16, QFont.Bold))
            self.logo_label.setStyleSheet("color: #4a9eff; background: transparent;")
        
        self.logo_label.setGraphicsEffect(self.create_shadow())
        self.logo_label.move(10, -10)  # Position accounting for the 30px window margin + 10px padding
        self.logo_label.raise_()  # Bring logo to front
        
        # Fade in effect
        self.opacity = 0.0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_in)
        self.fade_timer.start(50)
    
    def update_video_frame(self):
        if self.cap is None:
            return
        
        ret, frame = self.cap.read()
        
        if not ret:
            # Loop video - go back to start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        
        if ret:
            # Convert frame from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to QImage at original size
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Set to label - it will crop naturally if video is larger than window
            self.video_label.setPixmap(QPixmap.fromImage(q_image))
        
    
    def fade_in(self):
        if self.opacity < 1.0:
            self.opacity += 0.05
            self.welcome_label.setStyleSheet(f"color: rgba(255, 255, 255, {self.opacity}); background: transparent;")
            self.subtitle_label.setStyleSheet(f"color: rgba(255, 255, 255, {self.opacity}); background: transparent;")  # Changed to white
            # Reapply shadow effect after style change
            if self.opacity >= 1.0:
                self.welcome_label.setGraphicsEffect(self.create_shadow())
                self.subtitle_label.setGraphicsEffect(self.create_shadow())
        else:
            self.fade_timer.stop()
    
    def first_message_send(self):
        user_input = self.startup_input.text().strip()
        if not user_input:
            return
        
        self.first_message = user_input
        self.startup_input.setEnabled(False)
        self.startup_button.setEnabled(False)
        
        # Fade out and transition
        self.fade_out_timer = QTimer()
        self.fade_out_timer.timeout.connect(self.fade_out_welcome)
        self.fade_out_timer.start(30)
    
    def fade_out_welcome(self):
        if self.opacity > 0:
            self.opacity -= 0.1
            self.welcome_label.setStyleSheet(f"color: rgba(255, 255, 255, {max(0, self.opacity)}); background: transparent;")
            self.subtitle_label.setStyleSheet(f"color: rgba(255, 255, 255, {max(0, self.opacity)}); background: transparent;")  # Changed to white
        else:
            self.fade_out_timer.stop()
            self.show_chat_interface()
    
    def show_chat_interface(self):
        # Clear welcome screen
        self.welcome_container.hide()
        self.main_layout.removeWidget(self.welcome_container)
        
        # Clear stretch items
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        
        self.main_layout.addWidget(header)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(26, 43, 71, 100);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(74, 158, 255, 150);
                border-radius: 5px;
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        
        self.chat_scroll.setWidget(self.chat_widget)
        self.main_layout.addWidget(self.chat_scroll, 1)  # Give it stretch factor
        
        # Input area
        input_area = QWidget()
        input_area.setStyleSheet("background: transparent;")
        input_area.setFixedHeight(65)
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(0, 10, 0, 0)
        
        self.chat_input = QLineEdit()
        self.chat_input.setFont(QFont("Inter", 12))
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(26, 43, 71, 150);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton("→")
        send_button.setFont(QFont("Inter", 16, QFont.Bold))
        send_button.setFixedSize(50, 45)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        self.main_layout.addWidget(input_area)
        
        self.chat_state = True
        
        # Send first message
        if self.first_message:
            self.add_user_message(self.first_message)
            self.add_typing_indicator()
            self.worker = ChatWorker(self.first_message, self.room_number)
            self.worker.finished.connect(self.display_bot_response)
            self.worker.start()
        
        self.chat_input.setFocus()
    
    def create_shadow(self):
        """Create a drop shadow effect for widgets"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(2, 2)
        return shadow
    
    def add_user_message(self, message):
        msg_container = QWidget()
        msg_container.setStyleSheet("background: transparent;")
        msg_layout = QHBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.addStretch()
        
        bubble = QLabel(message)
        bubble.setFont(QFont("Inter", 11))
        bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 180);
                color: #1a1a1a;
                border-radius: 10px;
                padding: 10px 15px;
            }
        """)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(400)
        bubble.setGraphicsEffect(self.create_shadow())
        msg_layout.addWidget(bubble)
        
        self.chat_layout.addWidget(msg_container)
        self.scroll_to_bottom()
    
    def add_bot_message(self, message):
        msg_container = QWidget()
        msg_container.setStyleSheet("background: transparent;")
        msg_layout = QHBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tavv icon
        icon_label = QLabel()
        icon_path = r"C:\Users\Ocnarf\Tavv-Hotel-Assistant\pld-project-na-pamatay\media\icon.png"
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            icon_pixmap = icon_pixmap.scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
        else:
            # Fallback - show "T" text if icon not found
            icon_label.setText("T")
            icon_label.setFont(QFont("Inter", 14, QFont.Bold))
            icon_label.setStyleSheet("""
                background-color: #4a9eff;
                color: white;
                border-radius: 16px;
                padding: 6px;
            """)
            icon_label.setFixedSize(52, 52)
            icon_label.setAlignment(Qt.AlignCenter)
        
        icon_label.setGraphicsEffect(self.create_shadow())
        msg_layout.addWidget(icon_label, alignment=Qt.AlignTop)
        msg_layout.addSpacing(8)
        
        bubble = QLabel(message)
        bubble.setFont(QFont("Inter", 11))
        bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(26, 43, 71, 180);
                color: white;
                border-radius: 10px;
                padding: 10px 15px;
            }
        """)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(400)
        bubble.setGraphicsEffect(self.create_shadow())
        msg_layout.addWidget(bubble)
        msg_layout.addStretch()
        
        self.chat_layout.addWidget(msg_container)
        self.scroll_to_bottom()
    
    def add_typing_indicator(self):
        self.typing_container = QWidget()
        self.typing_container.setStyleSheet("background: transparent;")
        typing_layout = QHBoxLayout(self.typing_container)
        typing_layout.setContentsMargins(0, 0, 0, 0)
        
        typing_label = QLabel("Tavv is typing...")
        typing_label.setFont(QFont("Inter", 10))
        typing_label.setStyleSheet("""
            QLabel {
                background-color: rgba(26, 43, 71, 150);
                color: #888888;
                border-radius: 10px;
                padding: 8px 15px;
            }
        """)
        typing_label.setGraphicsEffect(self.create_shadow())
        typing_layout.addWidget(typing_label)
        typing_layout.addStretch()
        
        self.chat_layout.addWidget(self.typing_container)
        self.scroll_to_bottom()
    
    def remove_typing_indicator(self):
        if hasattr(self, 'typing_container'):
            self.chat_layout.removeWidget(self.typing_container)
            self.typing_container.deleteLater()
    
    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
    
    def send_message(self):
        user_input = self.chat_input.text().strip()
        if not user_input:
            return
        
        self.add_user_message(user_input)
        self.chat_input.clear()
        self.add_typing_indicator()
        
        self.worker = ChatWorker(user_input, self.room_number)
        self.worker.finished.connect(self.display_bot_response)
        self.worker.start()
    
    def display_bot_response(self, response):
        self.remove_typing_indicator()
        self.add_bot_message(response)

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Change "background.mp4" to your video file path
    window = TavvGUI(first_name, room, video_path=r"C:\Users\Ocnarf\Tavv-Hotel-Assistant\pld-project-na-pamatay\media\bg.mp4")
    window.show()
    sys.exit(app.exec_())