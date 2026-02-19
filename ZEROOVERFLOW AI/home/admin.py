from django.contrib import admin
from .models import GarbageBin, Complaint


@admin.register(GarbageBin)
class GarbageBinAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'fill_level', 'status', 'overflow_risk', 'last_emptied')
    list_filter = ('status', 'overflow_risk')
    search_fields = ('location',)
    list_editable = ('fill_level', 'status')
    ordering = ('-fill_level',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint_type', 'location', 'reported_by', 'status', 'created_at', 'gov_notified')
    list_filter = ('status', 'complaint_type', 'gov_notified')
    search_fields = ('location', 'reported_by', 'description')
    list_editable = ('status',)
    ordering = ('-created_at',)