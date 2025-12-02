from setup_env import setup_venv

setup_venv()

import os
from groq import Groq
import sqlite3
from hotel_db import DatabaseLoader


db = DatabaseLoader()  # create instance

# ----------------------------------
# READ TOKEN FROM DEVICE STORAGE
# ----------------------------------
def read_device_token(file_path):
    with open(file_path, "r") as f:
        return f.read().strip()

device1_token = read_device_token("device1_token.txt")
device2_token = read_device_token("device2_token.txt")
device3_token = read_device_token("device3_token.txt")


info = db.get_resident_from_token(device2_token)
name = info["name"]
room = info["room_number"]

if not info:
    print("ERROR: Your device token is not registered in the hotel system.")
    exit()

print(f"Launching Tavv...")
print("Hello,", name + "." )

#------------------------------
#Chat functions from here on out 
#------------------------------

db_path = os.path.join("data", "hotel.db")  # path to your DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Conversation memory per room
conversation_history = {}


def chat(user_input, room_number):
    if room_number not in conversation_history:
        conversation_history[room_number] = []

    # 1. Get Context Data from the updated hotel_db.py
    context_data = db.get_full_context(room_number)
    
    if not context_data:
        # This handles cases where the room is invalid
        return "Sorry, I couldn't find information for that room. Please check your room number."

    current_day = context_data.get('current_day', 'today') # Get day for context
    context_text = str(context_data)  # Convert entire context to string for Groq

    conversation ={
            #Prompt for Groq to begin acting like Tavv
            "role": "system", "content": (
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
                )}

    # Build message stack
    messages = [conversation, {"role": "user","content": f"Context:\n{context_text}\n\nUser question: {user_input}"}]

    # Add previous messages
    messages += conversation_history[room_number]

    # Add the new user message
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages  
    )

    reply =  response.choices[0].message.content

     # Save the exchange to memory
    conversation_history[room_number].append({"role": "user", "content": user_input})
    conversation_history[room_number].append({"role": "assistant", "content": reply})

    return reply 

# Chat main
if __name__ == "__main__":
    
    while True:
        msg = input("You: ")
        if msg.lower() in ["bye", "exit"]:
            print("Tavv: Goodbye! Enjoy your stay.")
            break
        print("Tavv:", chat(msg, room))

    
