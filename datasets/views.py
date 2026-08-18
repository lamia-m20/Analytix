from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import math
import logging

import pandas as pd

from analysis.models import AnalysisJob, AnalysisResult

from dashboards.services.dashboard_ai import (
    DashboardAIError,
)
from dashboards.services.dashboard_ai import (
    apply_dashboard_plan,
)
from dashboards.services.dashboard_ai import (
    build_dashboard_metadata,
)
from dashboards.services.dashboard_ai import (
    request_dashboard_plan,
)
from dashboards.services.dashboard_store import (
    get_or_create_dataset_dashboard,
)

from .forms import DatasetUploadForm
from .models import Dataset
from .services import create_dataset_structure
from .exporters import (
    ExportSourceError, build_csv_package, build_excel_report, build_pdf_report,
    build_report_data, load_workbook_data,
)
from .powerpoint import PPTX_CONTENT_TYPE, build_powerpoint_report

logger = logging.getLogger(__name__)


def _save_analysis_result(dataset, analysis_context):
    """Persist the upload analysis and initialise its dashboard exactly once."""
    sheet = dataset.sheets.order_by('index').first()
    if sheet is None:
        return None

    job, _ = AnalysisJob.objects.get_or_create(
        owner=dataset.user,
        dataset=dataset,
        sheet=sheet,
        analysis_type='descriptive',
        defaults={'name': dataset.title},
    )
    job.status = 'completed'
    job.progress = 100
    job.completed_at = timezone.now()
    job.error_message = ''
    job.save(update_fields=[
        'status', 'progress', 'completed_at', 'error_message', 'updated_at',
    ])

    result, _ = AnalysisResult.objects.update_or_create(
        analysis_job=job,
        defaults={
            'summary': analysis_context,
            'statistics': {
                key: analysis_context.get(key)
                for key in (
                    'sheets_count', 'total_rows', 'total_columns',
                    'total_missing_values', 'total_numeric_columns',
                )
            },
            'table_data': analysis_context.get('sheets_analysis', []),
            'rows_before_cleaning': analysis_context.get('total_rows', 0),
            'rows_after_cleaning': analysis_context.get('total_rows', 0),
        },
    )
    dashboard = get_or_create_dataset_dashboard(
        dataset,
        has_numeric_columns=bool(analysis_context.get('total_numeric_columns')),
    )
    dashboard.widgets.filter(analysis_result__isnull=True).update(
        analysis_result=result,
    )
    return result


def _get_saved_analysis(dataset):
    result = (
        AnalysisResult.objects
        .filter(
            analysis_job__dataset=dataset,
            analysis_job__owner=dataset.user,
            analysis_job__status='completed',
        )
        .order_by('-updated_at')
        .first()
    )
    return (result.summary, result) if result and result.summary else (None, None)


def _export_dataset(request, dataset_id, export_type):
    dataset = get_object_or_404(Dataset, pk=dataset_id, user=request.user)
    if dataset.status != 'ready' or not dataset.file:
        return HttpResponse('لا يمكن تصدير الملف قبل اكتمال التحليل.', status=409)
    try:
        frames = load_workbook_data(dataset)
        report_data = build_report_data(dataset, frames)
        if export_type == 'excel':
            stream, content_type, extension = build_excel_report(dataset, report_data), (
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ), '.xlsx'
        elif export_type == 'csv':
            stream, content_type, extension = build_csv_package(dataset, report_data)
        elif export_type == 'pdf':
            stream, content_type, extension = build_pdf_report(dataset, report_data), 'application/pdf', '.pdf'
        else:
            stream, content_type, extension = build_powerpoint_report(dataset, report_data), PPTX_CONTENT_TYPE, '.pptx'
    except ExportSourceError as error:
        return HttpResponse(str(error), status=503, content_type='text/plain; charset=utf-8')
    except Exception:
        logger.exception('Report export failed for dataset %s', dataset.pk)
        return HttpResponse(
            'تعذر تجهيز التقرير حاليًا. يرجى المحاولة مرة أخرى لاحقًا.',
            status=500,
            content_type='text/plain; charset=utf-8',
        )
    date_format = '%Y-%m-%d' if export_type == 'powerpoint' else '%Y%m%d'
    report_date = timezone.localdate().strftime(date_format)
    label = 'data' if export_type == 'csv' else 'report'
    filename = f'analytix_{label}_{dataset.pk}_{report_date}{extension}'
    return FileResponse(stream, as_attachment=True, filename=filename, content_type=content_type)


@login_required
def export_excel(request, dataset_id):
    return _export_dataset(request, dataset_id, 'excel')


@login_required
def export_csv(request, dataset_id):
    return _export_dataset(request, dataset_id, 'csv')


@login_required
def export_pdf(request, dataset_id):
    return _export_dataset(request, dataset_id, 'pdf')


@login_required
def export_powerpoint(request, dataset_id):
    return _export_dataset(request, dataset_id, 'powerpoint')


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


@login_required
def my_analyses(request):
    datasets = (
        Dataset.objects
        .filter(user=request.user)
        .prefetch_related('sheets', 'analysis_jobs__result')
        .order_by('-uploaded_at')
    )
    items = []
    for dataset in datasets:
        sheets = list(dataset.sheets.all())
        result = next(
            (
                job.result for job in dataset.analysis_jobs.all()
                if job.status == 'completed' and hasattr(job, 'result')
            ),
            None,
        )
        summary = result.summary if result else {}
        total_cells = sum(sheet.row_count * sheet.column_count for sheet in sheets)
        missing = summary.get('total_missing_values', 0)
        quality_score = (
            round(max(0, (1 - (missing / total_cells)) * 100), 1)
            if total_cells else None
        )
        items.append({
            'dataset': dataset,
            'sheets_count': len(sheets),
            'rows_count': summary.get(
                'total_rows', sum(sheet.row_count for sheet in sheets)
            ),
            'columns_count': summary.get(
                'total_columns', sum(sheet.column_count for sheet in sheets)
            ),
            'quality_score': quality_score,
            'dashboard': (
                dataset.user.dashboards.filter(
                    layout_settings__dataset_id=dataset.pk,
                ).first()
            ),
        })
    return render(request, 'datasets-templates/my_analyses.html', {'items': items})


@login_required
@require_POST
def edit_dashboard(request, dataset_id):
    dataset = get_object_or_404(
        Dataset.objects.prefetch_related(
            'sheets__columns'
        ),
        pk=dataset_id,
        user=request.user,
    )

    dashboard_request = request.POST.get(
        'dashboard_request',
        '',
    ).strip()

    if not dashboard_request:
        messages.error(
            request,
            'يرجى كتابة طلب تعديل الداشبورد.',
        )
        return redirect(
            'datasets:detail',
            pk=dataset.pk,
        )

    has_numeric_columns = any(
        any(
            marker in column.data_type.lower()
            for marker in (
                'int',
                'float',
                'decimal',
                'number',
            )
        )
        for sheet in dataset.sheets.all()
        for column in sheet.columns.all()
    )
    dashboard = get_or_create_dataset_dashboard(
        dataset,
        has_numeric_columns=has_numeric_columns,
    )
    metadata = build_dashboard_metadata(
        dataset,
        dashboard,
    )

    try:
        plan = request_dashboard_plan(
            user_request=dashboard_request,
            metadata=metadata,
        )
        applied_count = apply_dashboard_plan(
            dashboard=dashboard,
            user=request.user,
            metadata=metadata,
            plan=plan,
        )
    except DashboardAIError as error:
        messages.error(
            request,
            str(error),
        )
    else:
        messages.success(
            request,
            f'تم تعديل {applied_count} مخططات بنجاح.',
        )

    return redirect(
        'datasets:detail',
        pk=dataset.pk,
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


def _build_custom_widget_charts(
    excel_file,
    widgets,
):
    charts = []

    for widget in widgets:
        settings = widget.settings or {}
        if settings.get('source') != 'custom':
            continue

        sheet_name = settings.get('sheet_name')
        if (
            not sheet_name
            or not widget.x_column
            or not widget.y_column
        ):
            continue

        excel_file.seek(0)
        frame = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            usecols=list({
                widget.x_column,
                widget.y_column,
            }),
        )
        grouped = frame.groupby(
            widget.x_column,
            dropna=False,
        )[widget.y_column]

        if widget.aggregation == 'sum':
            values = grouped.sum()
        elif widget.aggregation == 'average':
            values = grouped.mean()
        else:
            values = grouped.count()

        charts.append(
            {
                'id': widget.pk,
                'title': widget.title,
                'chart_type': widget.widget_type,
                'colors': settings.get('colors', []),
                'labels': [
                    _display_value(value)
                    for value in values.index.tolist()
                ],
                'values': [
                    _rounded_number(value)
                    for value in values.tolist()
                ],
            }
        )

    return charts


def _add_dashboard_context(context, dashboard):
    for widget in dashboard.widgets.all():
        if not widget.is_visible:
            continue
        source = (widget.settings or {}).get('source')
        if source == 'sheet_dimensions':
            context['sheet_dimensions_widget'] = widget
            context['sheet_dimensions_colors'] = (widget.settings or {}).get('colors', [])
        elif source == 'missing_values':
            context['missing_values_widget'] = widget
            context['missing_values_colors'] = (widget.settings or {}).get('colors', [])
        elif source == 'numeric_means':
            context['numeric_means_widget'] = widget
            context['numeric_means_colors'] = (widget.settings or {}).get('colors', [])
        elif source == 'numeric_ranges':
            context['numeric_ranges_widget'] = widget
            context['numeric_ranges_colors'] = (widget.settings or {}).get('colors', [])


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
                uploaded_file.seek(0)
                analysis_context = _analyze_excel(uploaded_file)
                _save_analysis_result(dataset, analysis_context)

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

    context = {
        'dataset': dataset,
    }

    saved_context, _ = _get_saved_analysis(dataset)
    if saved_context:
        context.update(saved_context)
        dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=bool(context.get('total_numeric_columns')),
        )
        context['dashboard'] = dashboard
        _add_dashboard_context(context, dashboard)
    elif dataset.status == 'ready' and dataset.file:
        try:
            dataset.file.open('rb')
            context.update(
                _analyze_excel(dataset.file)
            )
            _save_analysis_result(dataset, context)

            dashboard = get_or_create_dataset_dashboard(
                dataset,
                has_numeric_columns=bool(
                    context['total_numeric_columns']
                ),
            )
            context['dashboard'] = dashboard
            _add_dashboard_context(context, dashboard)

            context['custom_widget_charts'] = (
                _build_custom_widget_charts(
                    dataset.file,
                    dashboard.widgets.filter(
                        is_visible=True
                    ),
                )
            )
        except Exception:
            context['error_message'] = (
                'تعذر إعادة عرض تحليل هذا الملف.'
            )
        finally:
            dataset.file.close()

    return render(
        request,
        'datasets-templates/dataset_home.html',
        context,
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
