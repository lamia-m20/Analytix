from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
import math

import pandas as pd

from .forms import DatasetUploadForm
from .models import Dataset
from .services import create_dataset_structure


@login_required
def dataset_list(request):
    context = {}

    if request.method == 'POST':
        uploaded_file = request.FILES.get(
            'excel_file'
        )

        if not uploaded_file:
            context['error_message'] = (
                'اختر ملف Excel أولًا.'
            )
        elif uploaded_file.size > 10 * 1024 * 1024:
            context['error_message'] = (
                'حجم الملف أكبر من الحد المسموح (10 ميجابايت).'
            )
        elif not uploaded_file.name.lower().endswith(
            ('.xlsx', '.xls', '.xlsm')
        ):
            context['error_message'] = (
                'صيغة الملف غير مدعومة. استخدم XLSX أو XLS أو XLSM.'
            )
        else:
            try:
                context.update(
                    _analyze_excel(uploaded_file)
                )
            except Exception:
                context['error_message'] = (
                    'تعذر قراءة الملف. تأكد من أنه ملف Excel سليم '
                    'وأن الصف الأول يحتوي على أسماء الأعمدة.'
                )

    return render(
        request,
        'datasets-templates/dataset_home.html',
        context,
    )


def _display_value(value):
    if pd.isna(value):
        return '—'

    if hasattr(value, 'isoformat'):
        return value.isoformat(
            sep=' ',
            timespec='seconds',
        )

    if isinstance(value, float):
        if not math.isfinite(value):
            return '—'
        return round(value, 3)

    return str(value)


def _rounded_number(value):
    if pd.isna(value) or not math.isfinite(float(value)):
        return None

    return round(float(value), 2)


def _analyze_excel(uploaded_file):
    uploaded_file.seek(0)
    workbook = pd.ExcelFile(uploaded_file)

    sheets_analysis = []
    chart_sheet_names = []
    chart_rows = []
    chart_columns = []
    chart_missing_values = []
    numeric_chart_labels = []
    numeric_chart_means = []
    numeric_chart_max_values = []
    numeric_chart_min_values = []

    total_rows = 0
    total_columns = 0
    total_missing_values = 0
    total_numeric_columns = 0

    for sheet_name in workbook.sheet_names:
        frame = workbook.parse(sheet_name=sheet_name)
        frame.columns = [
            str(column)
            for column in frame.columns
        ]

        rows_count = int(frame.shape[0])
        columns_count = int(frame.shape[1])
        missing_count = int(
            frame.isna().sum().sum()
        )
        numeric_frame = frame.select_dtypes(
            include='number'
        )
        numeric_columns_count = int(
            numeric_frame.shape[1]
        )

        column_types = [
            {
                'name': column,
                'type': str(frame[column].dtype),
            }
            for column in frame.columns
        ]
        missing_values = [
            {
                'column': column,
                'count': int(frame[column].isna().sum()),
            }
            for column in frame.columns
        ]
        numeric_statistics = []

        for column in numeric_frame.columns:
            series = numeric_frame[column].dropna()
            if series.empty:
                continue

            statistic = {
                'column': column,
                'count': int(series.count()),
                'mean': _rounded_number(series.mean()),
                'std': (
                    _rounded_number(series.std())
                    if len(series) > 1
                    else None
                ),
                'min': _rounded_number(series.min()),
                'max': _rounded_number(series.max()),
            }
            numeric_statistics.append(statistic)

            if len(numeric_chart_labels) < 16:
                numeric_chart_labels.append(
                    f'{sheet_name} — {column}'
                )
                numeric_chart_means.append(
                    statistic['mean']
                )
                numeric_chart_max_values.append(
                    statistic['max']
                )
                numeric_chart_min_values.append(
                    statistic['min']
                )

        preview = frame.head(10).copy()
        preview_rows = [
            {
                column: _display_value(value)
                for column, value in row.items()
            }
            for row in preview.to_dict(
                orient='records'
            )
        ]

        sheets_analysis.append(
            {
                'name': str(sheet_name),
                'has_data': columns_count > 0,
                'rows_count': rows_count,
                'columns_count': columns_count,
                'missing_count': missing_count,
                'numeric_columns_count': numeric_columns_count,
                'columns': list(frame.columns),
                'column_types': column_types,
                'missing_values': missing_values,
                'numeric_statistics': numeric_statistics,
                'preview_rows': preview_rows,
            }
        )

        chart_sheet_names.append(str(sheet_name))
        chart_rows.append(rows_count)
        chart_columns.append(columns_count)
        chart_missing_values.append(missing_count)
        total_rows += rows_count
        total_columns += columns_count
        total_missing_values += missing_count
        total_numeric_columns += numeric_columns_count

    return {
        'analysis_complete': True,
        'file_name': uploaded_file.name,
        'sheets_count': len(sheets_analysis),
        'total_rows': total_rows,
        'total_columns': total_columns,
        'total_missing_values': total_missing_values,
        'total_numeric_columns': total_numeric_columns,
        'sheets_analysis': sheets_analysis,
        'chart_sheet_names': chart_sheet_names,
        'chart_rows': chart_rows,
        'chart_columns': chart_columns,
        'chart_missing_values': chart_missing_values,
        'numeric_chart_labels': numeric_chart_labels,
        'numeric_chart_means': numeric_chart_means,
        'numeric_chart_max_values': numeric_chart_max_values,
        'numeric_chart_min_values': numeric_chart_min_values,
    }


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
