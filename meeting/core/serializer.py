from rest_framework import serializers

from .models import Schedules, Participant


class ParticipantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Participant
        fields = ["email"]

        
class CreateMeetingSerializer(serializers.ModelSerializer):
    
    inviter = serializers.CharField(read_only=True)  
    event_id = serializers.CharField(read_only=True)  
    class Meta:
        model = Schedules
        fields = ["summary","inviter","date","start_time","end_time","summary","event_id"]
        
    def create(self, validated_data):
        return super().create(validated_data)

        
class MultiInviteSerializer(serializers.ModelSerializer):
    
    date = serializers.CharField(read_only=True)
    summary = serializers.CharField(read_only=True)
    inviter = serializers.CharField(read_only=True)      
    end_time = serializers.CharField(read_only=True)
    event_id = serializers.CharField(required=True)
    start_time = serializers.CharField(read_only=True)
    participants = ParticipantSerializer(many=True,required=True)
    
    class Meta:
        model = Schedules
        fields = ["summary","inviter","date","start_time","end_time","participants","event_id"]
    
    def create(self, validated_data):
        return super().create(validated_data)