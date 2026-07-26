from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import DatasetUploadForm
from .models import Dataset
from .services import create_dataset_structure


@login_required
def dataset_list(request):
    datasets = (
        Dataset.objects
        .filter(
            user=request.user
        )
        .prefetch_related(
            'sheets'
        )
    )

    return render(
        request,
        'datasets/list.html',
        {
            'datasets': datasets,
        },
    )


@login_required
def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetUploadForm(
            request.POST,
            request.FILES,
            user=request.user,
        )

        if form.is_valid():
            uploaded_file = (
                form.cleaned_data['file']
            )

            dataset = form.save(
                commit=False
            )

            dataset.user = request.user
            dataset.original_filename = (
                uploaded_file.name
            )
            dataset.file_size = (
                uploaded_file.size
            )
            dataset.status = 'reading'

            dataset.save()

            try:
                create_dataset_structure(
                    dataset,
                    uploaded_file,
                )

            except Exception as error:
                dataset.status = 'failed'
                dataset.error_message = str(
                    error
                )

                dataset.save(
                    update_fields=[
                        'status',
                        'error_message',
                        'updated_at',
                    ],
                )

                messages.error(
                    request,
                    (
                        'تم رفع الملف، ولكن تعذرت '
                        'قراءة أوراق Excel. تأكد '
                        'من أن الملف سليم.'
                    ),
                )

                return redirect(
                    'datasets:detail',
                    pk=dataset.pk,
                )

            messages.success(
                request,
                (
                    'تم رفع ملف Excel '
                    'وتجهيزه بنجاح.'
                ),
            )

            return redirect(
                'datasets:detail',
                pk=dataset.pk,
            )

    else:
        form = DatasetUploadForm(
            user=request.user
        )

    return render(
        request,
        'datasets/upload.html',
        {
            'form': form,
        },
    )


@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(
        Dataset.objects.prefetch_related(
            'sheets__columns'
        ),
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        'datasets/detail.html',
        {
            'dataset': dataset,
        },
    )


@login_required
def delete_dataset(request, pk):
    dataset = get_object_or_404(
        Dataset,
        pk=pk,
        user=request.user,
    )

    if request.method == 'POST':
        if dataset.file:
            dataset.file.delete(
                save=False
            )

        dataset.delete()

        messages.success(
            request,
            'تم حذف ملف البيانات.',
        )

        return redirect(
            'datasets:list'
        )

    return render(
        request,
        'datasets/confirm_delete.html',
        {
            'dataset': dataset,
        },
    )