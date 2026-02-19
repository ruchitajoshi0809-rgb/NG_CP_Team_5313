from django.db import models
from django.utils import timezone

class GarbageBin(models.Model):
    location = models.CharField(max_length=200)
    fill_level = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='safe')
    last_emptied = models.DateTimeField(default=timezone.now)
    overflow_risk = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.location} - {self.fill_level}%"

class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ('overflow', 'Bin Overflow'),
        ('smell', 'Bad Odor'),
        ('damaged', 'Damaged Bin'),
        ('not_emptied', 'Not Emptied Regularly'),
        ('other', 'Other'),
    ]
    
    complaint_type = models.CharField(max_length=50, choices=COMPLAINT_TYPES)
    description = models.TextField()
    location = models.CharField(max_length=300)
    reported_by = models.CharField(max_length=100, default='Anonymous')
    contact_info = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved')
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ✅ FIXED INDENTATION HERE
    gov_notified = models.BooleanField(default=False)
    progress_percentage = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Complaint: {self.get_complaint_type_display()} at {self.location}"