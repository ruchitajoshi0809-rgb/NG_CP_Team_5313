from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import GarbageBin, Complaint  
from .ai_model import predict_overflow
from datetime import datetime
import json
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        # Check if user exists
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard') # Success -> Go to Govt Dashboard
        else:
            messages.error(request, "Invalid Credentials. Access Denied.")
    
    return render(request, 'home/login.html')

def logout_view(request):
    logout(request)
    return redirect('login') # Go back to login page

@login_required(login_url='login')  # <--- ADD THIS LINE

def dashboard(request):
    bins = GarbageBin.objects.all()

    # --- 1. AUTO-FILL SIMULATION ---
    for bin_obj in bins:
        try:
            time_diff = timezone.now() - bin_obj.last_emptied
            hours_passed = time_diff.total_seconds() / 3600
            new_fill_level = int(hours_passed * (100 / 480)) # 20 Day Cycle
            bin_obj.fill_level = min(100, new_fill_level)
            
            if bin_obj.fill_level >= 90: bin_obj.status = 'critical'
            elif bin_obj.fill_level >= 75: bin_obj.status = 'warning'
            else: bin_obj.status = 'safe'
            bin_obj.save()
        except: pass

    # --- 2. COUNTS ---
    total_count = bins.count()
    safe_count = bins.filter(status='safe').count()
    warning_count = bins.filter(status='warning').count()
    critical_count = bins.filter(status='critical').count()

    # --- 3. ALERTS ---
    critical_bins = bins.filter(status='critical')
    pending_complaints = Complaint.objects.filter(status='pending').order_by('-created_at')
    
    # --- 4. TASK MANAGEMENT (FIXED: Hide Resolved > 5 Days) ---
    
    # Calculate the date 5 days ago
    five_days_ago = timezone.now() - timedelta(days=5)

    # LOGIC: 
    # Show items that are PENDING or IN PROGRESS (Always show these)
    # OR
    # Show items that are RESOLVED but created within the last 5 days
    filtered_complaints = Complaint.objects.filter(
        Q(status__in=['pending', 'acknowledged']) | 
        Q(status='resolved', created_at__gte=five_days_ago)
    ).order_by('-created_at')

    # Get counts for the cards
    progress_count = Complaint.objects.filter(status='acknowledged').count()
    resolved_count = Complaint.objects.filter(status='resolved').count()

    return render(request, 'home/gov_dashboard.html', {
        'bins': bins,
        'recent_complaints': filtered_complaints, # <--- SENDING FILTERED LIST
        'pending_complaints': pending_complaints,
        'critical_bins': critical_bins,
        'total_count': total_count,
        'safe_count': safe_count,
        'warning_count': warning_count,
        'critical_count': critical_count,
        'progress_count': progress_count,
        'resolved_count': resolved_count
    })


def complaint(request):
    if request.method == 'POST':
        complaint_type = request.POST.get('complaint_type')
        location = request.POST.get('location')
        description = request.POST.get('description')
        
        Complaint.objects.create(
            complaint_type=complaint_type,
            location=location,
            description=description,
            status='pending',
            gov_notified=False
        )

        # ✅ SUCCESS MESSAGE
        messages.success(request, "✅ Complaint Submitted Successfully! The authorities have been notified.")
        
        return redirect('gov_dashboard')

    return render(request, 'home/complaint.html')
# --- API VIEWS (Keep as is) ---
def submit_complaint_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint = Complaint.objects.create(
                complaint_type=data.get('type'),
                location=data.get('location'),
                description=data.get('description'),
                reported_by=data.get('name', 'Anonymous'),
                contact_info=data.get('contact', ''),
                status='pending',
                gov_notified=False
            )
            return JsonResponse({'success': True, 'complaint_id': complaint.id, 'message': 'Complaint submitted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def get_recent_complaints(request):
    complaints = Complaint.objects.all().order_by('-created_at')[:10]
    data = []
    for complaint in complaints:
        data.append({
            'id': complaint.id,
            'type': complaint.get_complaint_type_display(),
            'location': complaint.location,
            'description': complaint.description[:100] + '...' if len(complaint.description) > 100 else complaint.description,
            'reported_by': complaint.reported_by,
            'status': complaint.status,
            'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
            'status_class': 'badge-warning' if complaint.status == 'pending' else 'badge-success'
        })
    return JsonResponse({'complaints': data})

def get_gov_alerts(request):
    recent_complaints = Complaint.objects.filter(gov_notified=False, status='pending').order_by('-created_at')
    critical_bins = GarbageBin.objects.filter(overflow_risk=True)
    alerts = []
    
    for complaint in recent_complaints:
        alerts.append({
            'type': 'complaint',
            'title': f'New Complaint: {complaint.get_complaint_type_display()}',
            'message': f'Reported at {complaint.location}',
            'details': complaint.description[:200],
            'complaint_id': complaint.id,
            'timestamp': complaint.created_at.isoformat(),
            'priority': 'high'
        })
        complaint.gov_notified = True
        complaint.save()

    for bin in critical_bins:
        alerts.append({
            'type': 'bin_overflow',
            'title': f'🚨 Bin Overflow Risk: {bin.location}',
            'message': f'Fill level: {bin.fill_level}%',
            'details': f'Last collected: {bin.last_emptied.strftime("%Y-%m-%d %H:%M")}',
            'bin_id': bin.id,
            'timestamp': timezone.now().isoformat(),
            'priority': 'critical'
        })

    return JsonResponse({'alerts': alerts})
from django.shortcuts import get_object_or_404, redirect

# Add this new view function to handle the "Mark Complete" button
def resolve_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint.status = 'resolved'
    complaint.gov_notified = True
    complaint.save()
    return redirect('dashboard')
# --- PASTE THIS AT THE VERY BOTTOM OF home/views.py ---

from django.shortcuts import get_object_or_404, redirect

# home/views.py

# home/views.py

from django.shortcuts import get_object_or_404, redirect
from .models import Complaint

def update_complaint_status(request, complaint_id, status_type):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # 1. HANDLE SLIDER UPDATE (POST Request)
    if request.method == 'POST' and status_type == 'custom':
        progress = int(request.POST.get('progress', 0)) # Get number from slider
        complaint.progress_percentage = progress
        
        # Auto-update status text based on number
        if progress == 100:
            complaint.status = 'resolved'
        elif progress > 0:
            complaint.status = 'acknowledged'
        else:
            complaint.status = 'pending'
            
        complaint.gov_notified = True
        complaint.save()
        return redirect('dashboard')

    # 2. HANDLE BUTTON CLICKS (GET Request - Start/Complete Buttons)
    if status_type == 'progress':
        complaint.status = 'acknowledged'
        complaint.progress_percentage = 50 # Default to 50% when clicking Start
        complaint.gov_notified = True
    elif status_type == 'resolved':
        complaint.status = 'resolved'
        complaint.progress_percentage = 100
        complaint.gov_notified = True
        
    complaint.save()
    return redirect('dashboard')

# home/views.py

from django.shortcuts import redirect
from django.utils import timezone

# ... other views ...

def dispatch_collection(request):
    # Find all bins that are Warning or Critical (>= 70%)
    critical_bins = GarbageBin.objects.filter(fill_level__gte=70)
    
    for bin_obj in critical_bins:
        bin_obj.fill_level = 0          # Empty the bin
        bin_obj.status = 'safe'         # Make it safe
        bin_obj.last_emptied = timezone.now() # Reset time
        bin_obj.save()
        
    # Redirect back to the Government Dashboard
    # Note: 'dashboard' is the NAME of your URL in urls.py
    return redirect('dashboard') 