from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Dashboard


def home(request):
    return render(request, 'home.html')


@login_required
def dashboard_list(request):
    dashboards = Dashboard.objects.filter(owner=request.user).prefetch_related('widgets')
    return render(
        request,
        'dashboards-templates/list.html',
        {'dashboards': dashboards},
    )
