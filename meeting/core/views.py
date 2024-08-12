import os
from oauth2client import file
from oauth2client import client, tools
from rest_framework.response import Response
from dotenv import load_dotenv, find_dotenv
from rest_framework import routers, viewsets, mixins, status

from .models import Schedules, Participant
from .serializer import (
    ParticipantSerializer,
    MultiInviteSerializer,
    CreateMeetingSerializer,
    )
from .utils import ( 
    credentials,
    client_secret,
    create_event,
    update_event,
    overlap_schedule,
    participant_utils,
    get_calendar_email,
    existing_schedules_utils,
    convert_date_time_to_standard,
    check_participants_overlap_schedule,
    createview_existing_schedules_utils,
    )


load_dotenv(find_dotenv())


class GoogleCalendarAuthView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A view that handles Google Calendar API authentication.
    """
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    
    def get_credentials(self):
        store = file.Storage(credentials)
        creds = store.get()

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(client_secret, os.getenv("SCOPES"))
            tools.run_flow(flow, store)
            creds = store.get()

        return creds

    def list(self, request, *args, **kwargs):            
        creds = self.get_credentials()
        if creds:
            return Response({"message": "Authentication successful"}, status=status.HTTP_200_OK)
        else:
            return super().list(request, *args, **kwargs)
        
    
class CreateMeeting(mixins.ListModelMixin,viewsets.GenericViewSet):
    
    """
    Class based view that create events in google calendar
        - summary : str
        - start_time : time
        - end_time : time
        - date : date
    """
    
    queryset = Schedules.objects.all()
    serializer_class = CreateMeetingSerializer
    
    def create(self, request):
        
        serializer = CreateMeetingSerializer(data = request.data)
        
        if serializer.is_valid():
            inviter = get_calendar_email("primary")
            date = str(serializer.validated_data["date"])
            summary = serializer.validated_data["summary"]
            end_time = str(serializer.validated_data["end_time"])
            start_time = str(serializer.validated_data["start_time"])
            con_end_time = convert_date_time_to_standard(date,end_time)
            con_start_time = convert_date_time_to_standard(date,start_time)
            
            existing_schedules = createview_existing_schedules_utils(Schedules=Schedules,inviter=inviter,event_schedule=con_start_time)

            for schedule in existing_schedules:
                if not (con_end_time["time"] <= schedule.start_time or con_start_time["time"] >= schedule.end_time):
                    return Response({"error": f"{inviter} has an overlapping meeting at this time : {con_start_time['time']}."}, status=status.HTTP_400_BAD_REQUEST)

            response = create_event(calendar_id="primary",summary=summary,start_time=con_start_time["datetime"],end_time=con_end_time["datetime"])
            schedule = serializer.save(summary=summary,event_id=response['id'],inviter=inviter,date=con_start_time["date"],start_time=con_start_time["time"],end_time=con_end_time["time"])

            return Response({"success": "Meeting scheduled successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
                
                
class InviteWithRoom(mixins.ListModelMixin,viewsets.GenericViewSet):
    
    """
    Class based view that add the participants in the existing events in google calendar using event id and list of participants.
        - event_id = "ksngklnNLMvl"
        - participants = [{"email":"jagadish.nadar41@gmail.com","name":"jagadish"}] (email-required, name-optional)
    """
    
    queryset = Schedules.objects.all()
    serializer_class = MultiInviteSerializer
    
    def create(self, request):
        
        serializer = MultiInviteSerializer(data = request.data)
        if serializer.is_valid():
            part_sch = {"available":[],"unavailable":[]}
            inviter = get_calendar_email("primary")
            participants_data = serializer.validated_data["participants"]
            event_id = serializer.validated_data["event_id"]            
            participant, created = Participant.objects.get_or_create(
                email=inviter, defaults={"name": str(inviter).split('@')[0]}
            )
            
            room_schedule = Schedules.objects.filter(
                event_id = event_id
            )
            
            if room_schedule.exists():
                
                event_schedule = room_schedule[0]
                participants_qs = event_schedule.participants.all()
                
                participant_match = {"email": str(inviter)} in list(
                    map(lambda item: {"email": item.email}, participants_qs)
                )
                if (participant_match or event_schedule.inviter == inviter) and len(participants_data) != 0:
                    check_participants_overlap_schedule(participants_data,Participant,Schedules,event_schedule,part_sch)                        
                else:
                    participant, created = participant_utils(Participant=Participant,inviter=inviter)
                    existing_schedules = existing_schedules_utils(Schedules=Schedules,inviter=inviter,event_schedule=event_schedule,participant=participant)
                    overlap_schedule(existing_schedules=existing_schedules,event_schedule=event_schedule,inviter=inviter,room_schedule=room_schedule)
                    check_participants_overlap_schedule(participants_data,Participant,Schedules,event_schedule,part_sch)
                    
                print(part_sch["available"])
                body = {
                    'summary': event_schedule.summary,
                    'start': {
                        'dateTime': f"{event_schedule.date}T{event_schedule.start_time}+00:00",
                        'timeZone': 'Asia/Kolkata',  # Change to your timezone
                    },
                    'end': {
                        'dateTime': f"{event_schedule.date}T{event_schedule.end_time}+00:00",
                        'timeZone': 'Asia/Kolkata',  # Change to your timezone
                    },
                    'attendees' : part_sch["available"]
                }
                
                update_event("primary",event_id,body)
                
            else:
                return Response({"Error":"Event Id is Invalid"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"success": f"Meeting scheduled successfully for {part_sch['available']} and this are busy participants {part_sch['unavailable']}."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
                
                
router = routers.DefaultRouter()
router.register(r'Create Event', CreateMeeting, basename='create_event')
router.register(r'Add Participants', InviteWithRoom, basename='add_participants')
router.register(r'start with google calendar authentication', GoogleCalendarAuthView, basename="auth")