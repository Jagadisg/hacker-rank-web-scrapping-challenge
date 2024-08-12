from django.db import models

class Participant(models.Model):
    
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.email


class Schedules(models.Model):
    
    date = models.DateField()
    inviter = models.EmailField()
    end_time = models.TimeField()
    start_time = models.TimeField()
    event_id = models.CharField(max_length=100)
    participants = models.ManyToManyField(Participant)
    summary = models.CharField(max_length=300, default="No Summary",blank=True,null=True)

    def __str__(self):
        return f"{self.participants} from {self.start_time} to {self.end_time}"    