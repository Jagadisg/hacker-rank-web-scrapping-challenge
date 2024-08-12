import os
import uuid
import datetime
from oauth2client import file
from rest_framework import status
from dotenv import load_dotenv, find_dotenv
from googleapiclient.discovery import build
from rest_framework.response import Response

load_dotenv(find_dotenv())


def file_location(file_name):
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name)
    return dotenv_path

env = file_location(".env")
client_secret = file_location('client_secret.json')
credentials = file_location('credentials.json')


def get_calendar_email(calendar_id):
    store = file.Storage(credentials)
    creds = store.get()
    service = build('calendar', 'v3', credentials=creds)
    calendar = service.calendarList().get(calendarId=calendar_id).execute()
    print(calendar)
    return calendar.get('id')


def create_event(calendar_id: str, summary: str, start_time: str, end_time: str, attendees: list|None = None):
    
    '''Function view Create event in the google calendar'''
    
    store = file.Storage(credentials)
    creds = store.get()
    service = build('calendar', 'v3', credentials=creds)
    attendees = attendees if attendees is not None else []
    
    event = {
        'summary': summary,
        'location':"Somewhere Online",
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata',  
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',  
        },
        'attendees': [{'email': email} for email in attendees],
        'conferenceData': {
            'createRequest': {
                'requestId': str(uuid.uuid4()),
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet',
                },
            },
        },
    }

    event = service.events().insert(calendarId=calendar_id, body=event,
                                    conferenceDataVersion=1).execute()
 
    return event


def update_event(calendar_id: str,event_id: str,body: dict):
    
    store = file.Storage(credentials)
    creds = store.get()
    service = build('calendar', 'v3', credentials=creds)
    service.events().update(calendarId=calendar_id,eventId=event_id,body=body).execute()


def check_name_in_input(participant_data):
    
    if participant_data.get("name"):
        name = participant_data["name"]
    else:
        name = participant_data["email"].split('@')[0]
    return name
    
    
def convert_time_to_standard(input_time):
    
    try:
        # Handle 12-hour format with AM/PM
        if 'am' in input_time.lower() or 'pm' in input_time.lower():
            if ":" in input_time:
                time_obj = datetime.datetime.strptime(input_time, "%I:%M %p")
            else:
                time_obj = datetime.datetime.strptime(input_time, "%I %p")
            return time_obj.time()

        # Handle 24-hour format with colon
        elif ':' in input_time:
            time_obj = datetime.datetime.strptime(input_time, "%H:%M:%S")
            return time_obj.time()

        # Handle 24-hour format without minutes
        else:
            hour = int(input_time)
            if hour < 0 or hour > 23:
                raise ValueError("Hour must be between 0 and 23.")
            time_obj = datetime.datetime.strptime(f"{hour}:00", "%H:%M")
            return time_obj.time()

    except ValueError as e:
        return f"Error: {e}"


def convert_date_time_to_standard(date_str, time_str):
    # Convert time to a datetime object
    time_obj = convert_time_to_standard(time_str)
    
    if isinstance(time_obj, str) and time_obj.startswith("Error"):
        return time_obj  # Return the error message if any
    
    # Define the standard date formats to check
    date_formats = ["%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d"]
    
    for date_format in date_formats:
        try:
            # Parse the date
            date_obj = datetime.datetime.strptime(date_str, date_format)
            date = str(date_obj.date())
            time = str(time_obj)
            return {"date":date,"time":time,"datetime":f"{date}T{time}+00:00"}
        except ValueError:
            continue

    return "Error: Invalid date format"


def participant_utils(Participant,inviter):
    participant, created = Participant.objects.get_or_create(
                            email=inviter, defaults={"name": str(inviter).split('@')[0]}
                        )
    return participant, created


def existing_schedules_utils(Schedules,inviter,event_schedule,participant):
    existing_schedules = Schedules.objects.filter(
        inviter=inviter,
        date=event_schedule.date,
        participants=participant
        )
    return existing_schedules


def createview_existing_schedules_utils(Schedules,inviter,event_schedule):
    existing_schedules = Schedules.objects.filter(
        inviter=inviter,
        date=event_schedule["date"],
        )
    return existing_schedules


def overlap_schedule(existing_schedules,event_schedule,room_schedule,inviter):
    for schedule in existing_schedules:
        if not (event_schedule.end_time <= schedule.start_time or event_schedule.start_time >= schedule.end_time):
            return Response({"error": f"{inviter} has an overlapping meeting at this time : {room_schedule[0].start_time}."}, status=status.HTTP_400_BAD_REQUEST)
        
        
def check_participants_overlap_schedule(participants_data,Participant,Schedules,event_schedule,part_sch):
    for participant_data in participants_data:
        participant, created = Participant.objects.get_or_create(
            email=participant_data["email"], defaults={"name": check_name_in_input(participant_data)}
        )

        participant_schedules = Schedules.objects.filter(
            participants=participant,
            date=event_schedule.date,
            inviter=participant_data["email"]
        )
        
        for schedule in participant_schedules:
            if not (event_schedule.end_time <= schedule.start_time or event_schedule.start_time >= schedule.end_time):
                part_sch["unavailable"].append({"email":participant_data["email"]})                        
        part_sch["available"].append({"email":participant_data["email"]})

        event_schedule.participants.add(participant)