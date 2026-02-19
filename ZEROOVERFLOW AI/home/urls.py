from django.urls import path
from . import views
from government import views as user_views # Import User Dashboard View

urlpatterns = [
    # 1. Homepage is PUBLIC User Dashboard
    path('', user_views.gov_dashboard, name='gov_dashboard'),

    # 2. Login & Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 3. Protected Govt Dashboard
    path('government-dashboard/', views.dashboard, name='dashboard'),

    # ... Your other URLs (dispatch, complaint, update-status) ...
    path('dispatch/', views.dispatch_collection, name='dispatch_collection'),
    path('complaint/', views.complaint, name='complaint'),
    path('update-status/<int:complaint_id>/<str:status_type>/', views.update_complaint_status, name='update_status'),
]