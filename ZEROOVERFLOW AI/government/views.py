from django.shortcuts import render
from django.utils import timezone
from home.models import GarbageBin, Complaint
from home.ai_model import predict_overflow

def gov_dashboard(request):
    # 1. Fetch all bins
    all_bins = GarbageBin.objects.all()

    # 2. Group bins by City (Noida, Ghaziabad, etc.)
    city_groups = {
        'Noida': [],
        'Ghaziabad': [],
        'Janakpuri': [],
        'Dwarka': [],
        'Gurugram': []
    }
    
    for bin_obj in all_bins:
        # Update AI
        hours = (timezone.now() - bin_obj.last_emptied).total_seconds() / 3600
        bin_obj.overflow_risk = predict_overflow(bin_obj.fill_level, hours)
        bin_obj.save()
        
        # Sort into cities
        added = False
        for city in city_groups.keys():
            if city in bin_obj.location:
                city_groups[city].append(bin_obj)
                added = True
                break

    # 3. Stats
    total_bins = all_bins.count()
    safe_bins = all_bins.filter(status='safe').count()
    warning_bins = all_bins.filter(status='warning').count()
    critical_bins = all_bins.filter(status='critical').count()
    
    # 4. Complaints
    complaints = Complaint.objects.all().order_by('-created_at')

    context = {
        'city_groups': city_groups,
        'all_bins': all_bins,       # Needed for Map & Dropdown
        'complaints': complaints,
        'total_bins': total_bins,
        'safe_bins': safe_bins,
        'warning_bins': warning_bins,
        'critical_bins': critical_bins,
    }

    return render(request, 'government/user_dashboard.html', context)