import streamlit as st
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import pickle
from google.auth.transport.requests import Request

# Authenticate and create a calendar instance
def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    # Check if token.pickle exists for stored user credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use Streamlit secrets for client_id and client_secret
            client_id = st.secrets["google"]["client_id"]
            client_secret = st.secrets["google"]["client_secret"]
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                },
                SCOPES
            )
            # Using run_console instead of run_local_server
            if st.session_state.get("auth_code") is None:
                auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
                st.markdown(f'**Authorize the app by visiting this URL:** [Authorize]({auth_url})')
                st.text_input("Enter the authorization code here:", key="auth_code")

            # After entering the authorization code
            if st.session_state.get("auth_code"):
                flow.fetch_token(code=st.session_state["auth_code"])
                creds = flow.credentials

                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

    calendar_service = build('calendar', 'v3', credentials=creds)
    return calendar_service


# Create an event
def create_event(calendar_service, summary, location, description, start, end, attendees):
    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Europe/Tirane',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Europe/Tirane',
        },
        'attendees': [{'email': attendee.strip()} for attendee in attendees if attendee],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    
    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    st.success(f"Event created: {event.get('htmlLink')}")

# Update an event
def update_event(calendar_service, event_id, summary, location, description, start, end, attendees):
    event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
    
    event['summary'] = summary
    event['location'] = location
    event['description'] = description
    event['start'] = {'dateTime': start.isoformat(), 'timeZone': 'Europe/Tirane'}
    event['end'] = {'dateTime': end.isoformat(), 'timeZone': 'Europe/Tirane'}
    event['attendees'] = [{'email': attendee.strip()} for attendee in attendees if attendee]

    updated_event = calendar_service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    st.success(f"Event updated: {updated_event.get('htmlLink')}")

# Delete an event
def delete_event(calendar_service, event_id):
    calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
    st.success("Event deleted successfully.")

# Display existing events in a table
def display_events(calendar_service):
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = calendar_service.events().list(calendarId='primary', timeMin=now,
                                                    maxResults=10, singleEvents=True,
                                                    orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        st.write('No upcoming events found.')
        return []

    event_data = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        event_data.append({
            'id': event['id'],
            'Summary': event['summary'],
            'Start': start,
            'Location': event.get('location', 'N/A'),
            'Description': event.get('description', 'N/A'),
            'Attendees': ', '.join([attendee['email'] for attendee in event.get('attendees', [])]),
            'Link': event.get('htmlLink')
        })
    
    # Create a DataFrame to display as a table
    st.table(event_data)
    return event_data  # Return event data for selection

# Main function
def main():
    st.title("Google Calendar Management")

    # Authenticate and create a calendar instance
    calendar_service = authenticate_google_calendar()

    # Create a row for event management forms
    st.subheader("Event Management")

    # Create a new event
    col1, col2, col3 = st.columns(3)  # Three equal columns for forms

    with col1:
        with st.form("create_event"):
            st.markdown("### Create Event")
            summary = st.text_input("Event Summary")
            location = st.text_input("Event Location")
            description = st.text_area("Event Description")

            start_date = st.date_input("Start Date", value=datetime.now().date())
            start_time = st.time_input("Start Time", value=datetime.now().time())
            start = datetime.combine(start_date, start_time)

            end_date = st.date_input("End Date", value=datetime.now().date())
            end_time = st.time_input("End Time", value=datetime.now().time())
            end = datetime.combine(end_date, end_time)

            attendees = st.text_input("Attendees (comma-separated)").split(',')

            submit_button = st.form_submit_button("Create Event")
            if submit_button:
                create_event(calendar_service, summary, location, description, start, end, attendees)

    with col2:
        with st.form("update_event"):
            st.markdown("### Update Event")
            event_id = st.text_input("Event ID (from existing events)", value=st.session_state.get("event_id", ""))
            summary = st.text_input("New Event Summary", value=st.session_state.get("summary", ""))
            location = st.text_input("New Event Location", value=st.session_state.get("location", ""))
            description = st.text_area("New Event Description", value=st.session_state.get("description", ""))

            start_date = st.date_input("New Start Date", value=st.session_state.get("start_date", datetime.now().date()))
            start_time = st.time_input("New Start Time", value=st.session_state.get("start_time", datetime.now().time()))
            start = datetime.combine(start_date, start_time)

            end_date = st.date_input("New End Date", value=st.session_state.get("end_date", datetime.now().date()))
            end_time = st.time_input("New End Time", value=st.session_state.get("end_time", datetime.now().time()))
            end = datetime.combine(end_date, end_time)

            attendees = st.text_input("New Attendees (comma-separated)", value=st.session_state.get("attendees", "")).split(',')

            update_button = st.form_submit_button("Update Event")
            if update_button:
                update_event(calendar_service, event_id, summary, location, description, start, end, attendees)
                
                # Clear the fields after successful update
                st.session_state["event_id"] = ""
                st.session_state["summary"] = ""
                st.session_state["location"] = ""
                st.session_state["description"] = ""
                st.session_state["start_date"] = datetime.now().date()
                st.session_state["start_time"] = datetime.now().time()
                st.session_state["end_date"] = datetime.now().date()
                st.session_state["end_time"] = datetime.now().time()
                st.session_state["attendees"] = ""

    with col3:
        with st.form("delete_event"):
            st.markdown("### Delete Event")
            event_id_to_delete = st.text_input("Event ID to delete")
            delete_button = st.form_submit_button("Delete Event")
            if delete_button:
                delete_event(calendar_service, event_id_to_delete)

    # Display calendar below forms
    st.subheader("Your Google Calendar")
    public_calendar_url = "https://calendar.google.com/calendar/embed?src=shpresakushta%40gmail.com&ctz=Europe%2FTirane"
    st.markdown(f'<iframe src="{public_calendar_url}" style="border: 0; width: 100%; height: 600px;" frameborder="0"></iframe>', unsafe_allow_html=True)

    # Display existing events and capture data for selection
    st.subheader("Existing Events")
    event_data = display_events(calendar_service)

    # Form to show details of the selected event
    st.subheader("Event Details")
    if event_data:
        selected_event_summary = st.selectbox("Select an Event", [event['Summary'] for event in event_data])
        
        if selected_event_summary:
            # Fetch details of the selected event
            selected_event = next(event for event in event_data if event['Summary'] == selected_event_summary)
            st.session_state["event_id"] = selected_event['id']
            st.session_state["summary"] = selected_event['Summary']
            st.session_state["location"] = selected_event['Location']
            st.session_state["description"] = selected_event['Description']
            st.session_state["attendees"] = selected_event['Attendees']
            st.session_state["start_date"] = selected_event['Start']
            # You can store more information in session_state if needed

if __name__ == "__main__":
    main()
