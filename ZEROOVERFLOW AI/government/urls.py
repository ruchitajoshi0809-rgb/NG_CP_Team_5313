from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.gov_dashboard, name='gov_dashboard'),
]
