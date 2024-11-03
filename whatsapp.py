import requests
import json
import os

def fetch_logs(file_path):
    """Reads the log file content."""
    with open(file_path, 'r') as file:
        logs = file.read()
    return logs

def analyze_logs(log_content):
    """Sends the log content to the Gemini API for analysis."""
    url = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"

    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Give One line brief suggestions on the log analysis provided.\n\n"+log_content  # Send the actual log content
            }
        ],
        "model": "gpt-4o",
        "max_tokens": 100,
        "temperature": 0.9
    }

    headers = {
        "x-rapidapi-key": "09de0418fdmsh6abcff074af2ca4p15cd43jsnd092871ea295",  # Use environment variable for API key
        "x-rapidapi-host": "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    # Sending request to Gemini API
    response = requests.post(url, json=payload, headers=headers)

    # Check for success
    if response.status_code == 200:
        response_data = response.json()
        # Debugging: Print the entire response data
        print("Response Data:", json.dumps(response_data, indent=2))  # Pretty-print the response

        # Check if the expected keys are present
        if 'choices' in response_data and len(response_data['choices']) > 0:
            suggestions = response_data['choices'][0]['message']['content']
            return suggestions
        else:
            print("No suggestions found in the response.")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


# Fetch and analyze logs
log_file = '/root/stress_test.log'
log_content = fetch_logs(log_file)
suggestions = analyze_logs(log_content)

# Save suggestions to a file if analysis was successful
if suggestions:
    with open('suggestions.txt', 'w') as file:
        file.write(suggestions)
    print("Suggestions saved to 'suggestions.txt'")
else:
    print("No suggestions available due to API error.")
SCRIPT >cat whatsapp.py
from twilio.rest import Client
def send_to_whatsapp(suggestions):
    # Twilio credentials
    account_sid = ''  # Replace with your Twilio Account SID
    auth_token = ''    # Replace with your Twilio Auth Token
    whatsapp_number = 'whatsapp:+14155238886'  # Twilio Sandbox WhatsApp number
    recipient_number = 'whatsapp:+91'  # Your WhatsApp number

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Send the message
    message = client.messages.create(
        from_=whatsapp_number,
        body=f"Suggestions from log analysis:\n{suggestions}",
        to=recipient_number
    )
    print(f"Message sent with SID: {message.sid}")

# Read the suggestions from 'suggestions.txt'
with open('suggestions.txt', 'r') as file:
    suggestions = file.read()

# Send suggestions to WhatsApp
send_to_whatsapp(suggestions)
