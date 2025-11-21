import os
from groq import Groq
import sqlite3
from hotel_db import DatabaseLoader


db = DatabaseLoader()  # create instance

# ----------------------------------
# READ TOKEN FROM DEVICE STORAGE
# ----------------------------------
with open("device_token.txt", "r") as f:
    device_token = f.read().strip()

info = db.get_resident_from_token(device_token)
name = info["name"]
room = info["room_number"]

if not info:
    print("ERROR: Your device token is not registered in the hotel system.")
    exit()

print(f"Authenticated as room {room}.\nLaunching Tavv...")
print("Hello", name )

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
                "When the user asks, try NOT to add instructions or steps unless the user explicitly requests: explain, how do I, or steps."
                #Language accomodation
                "Speak in user's language.")}



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
    
    
