import streamlit as st
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Authenticate and create a calendar instance using service account
def authenticate_google_calendar():
    # Load the credentials from Streamlit secrets
    calendar_api = st.secrets["CalendarAPI"]
    
    # Create a service account credentials object
    credentials = service_account.Credentials.from_service_account_info(calendar_api)

    # Build the Google Calendar service
    calendar_service = build('calendar', 'v3', credentials=credentials)
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
            st.write(f"### Summary: {selected_event['Summary']}")
            st.write(f"**Start:** {selected_event['Start']}")
            st.write(f"**Location:** {selected_event['Location']}")
            st.write(f"**Description:** {selected_event['Description']}")
            st.write(f"**Attendees:** {selected_event['Attendees']}")
            st.markdown(f"[View Event]({selected_event['Link']})")

if __name__ == "__main__":
    main()
