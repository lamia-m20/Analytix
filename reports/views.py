from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from datasets.models import Dataset


@login_required
def report_list(request):
    datasets = Dataset.objects.filter(user=request.user, status='ready')
    return render(request, 'reports-templates/list.html', {'datasets': datasets})
