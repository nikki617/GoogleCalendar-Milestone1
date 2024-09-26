import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Function to authenticate with Google Calendar API
def authenticate_google_calendar():
    # Load the credentials from Streamlit secrets
    credentials_info = st.secrets["gcp_service_account"]
    
    creds = service_account.Credentials.from_service_account_info(
        credentials_info
    )
    
    # Create the Google Calendar service
    calendar_service = build('calendar', 'v3', credentials=creds)
    return calendar_service

# Function to create an event
def create_event(calendar_service, event_details):
    event = {
        'summary': event_details['summary'],
        'location': event_details['location'],
        'description': event_details['description'],
        'start': {
            'dateTime': event_details['start'],
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': event_details['end'],
            'timeZone': 'UTC',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 10},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    return event

# Streamlit app layout
st.title("Google Calendar Event Creator")

# Event input fields
summary = st.text_input("Event Summary", "")
location = st.text_input("Event Location", "")
description = st.text_area("Event Description", "")
start_time = st.datetime_input("Start Time")
end_time = st.datetime_input("End Time")

# Create event button
if st.button("Create Event"):
    if summary and start_time and end_time:
        calendar_service = authenticate_google_calendar()
        
        event_details = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
        }
        
        event = create_event(calendar_service, event_details)
        st.success(f"Event created: {event.get('htmlLink')}")
    else:
        st.error("Please fill in all required fields.")
