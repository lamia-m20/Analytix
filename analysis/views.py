from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AnalysisJob


@login_required
def analysis_list(request):
    analyses = (
        AnalysisJob.objects
        .filter(owner=request.user)
        .select_related('dataset', 'sheet')
        .order_by('-created_at')
    )
    return render(request, 'analysis-templates/list.html', {'analyses': analyses})
