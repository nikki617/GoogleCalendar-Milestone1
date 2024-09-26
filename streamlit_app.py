import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Streamlit app title
st.title("Google Calendar Events")

# Load the service account credentials from Streamlit secrets
credentials_info = {
    "type": st.secrets["CalendarAPI"]["type"],
    "project_id": st.secrets["CalendarAPI"]["project_id"],
    "private_key_id": st.secrets["CalendarAPI"]["private_key_id"],
    "private_key": st.secrets["CalendarAPI"]["private_key"].replace("\\n", "\n"),  # Replace escaped newline
    "client_email": st.secrets["CalendarAPI"]["client_email"],
    "client_id": st.secrets["CalendarAPI"]["client_id"],
    "auth_uri": st.secrets["CalendarAPI"]["auth_uri"],
    "token_uri": st.secrets["CalendarAPI"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["CalendarAPI"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["CalendarAPI"]["client_x509_cert_url"],
    "universe_domain": st.secrets["CalendarAPI"]["universe_domain"],
}

# Create credentials from the loaded info
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Build the Google Calendar API service
service = build('calendar', 'v3', credentials=credentials)

# Example: list calendar events
calendar_id = 'primary'

try:
    # Fetch the upcoming events
    events_result = service.events().list(calendarId=calendar_id, maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    # Display events
    if not events:
        st.write('No upcoming events found.')
    else:
        st.write("Upcoming events:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            st.write(f"{start} - {event['summary']}")
except Exception as e:
    st.error(f"An error occurred: {e}")
