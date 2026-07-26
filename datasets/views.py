from pathlib import Path

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = [
    '.xlsx',
    '.xls',
]


def safe_number(value):
    """
    تحويل قيم Pandas وNumPy إلى قيم مناسبة
    لإرسالها إلى قالب Django وJavaScript.
    """

    if pd.isna(value):
        return None

    try:
        return round(float(value), 2)

    except (TypeError, ValueError):
        return value


@login_required(login_url='accounts:login')
def dataset_home(request):
    context = {}

    if request.method == 'POST':
        uploaded_file = request.FILES.get('excel_file')

        if not uploaded_file:
            context['error_message'] = (
                'يرجى اختيار ملف Excel أولًا.'
            )

            return render(
                request,
                'datasets-templates/dataset_home.html',
                context,
            )

        file_extension = Path(
            uploaded_file.name
        ).suffix.lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            context['error_message'] = (
                'صيغة الملف غير مدعومة. '
                'يرجى رفع ملف بصيغة XLSX أو XLS.'
            )

            return render(
                request,
                'datasets-templates/dataset_home.html',
                context,
            )

        if uploaded_file.size > MAX_FILE_SIZE:
            context['error_message'] = (
                'حجم الملف كبير جدًا. '
                'الحد الأعلى المسموح هو 10 ميجابايت.'
            )

            return render(
                request,
                'datasets-templates/dataset_home.html',
                context,
            )

        try:
            # قراءة جميع أوراق ملف Excel
            excel_sheets = pd.read_excel(
                uploaded_file,
                sheet_name=None,
            )

            if not excel_sheets:
                context['error_message'] = (
                    'ملف Excel لا يحتوي على أوراق بيانات.'
                )

                return render(
                    request,
                    'datasets-templates/dataset_home.html',
                    context,
                )

            sheets_analysis = []

            total_rows = 0
            total_columns = 0
            total_missing_values = 0
            total_numeric_columns = 0

            chart_sheet_names = []
            chart_rows = []
            chart_columns = []
            chart_missing_values = []

            numeric_chart_labels = []
            numeric_chart_means = []
            numeric_chart_max_values = []
            numeric_chart_min_values = []

            for sheet_name, dataframe in excel_sheets.items():
                # حذف الصفوف الفارغة بالكامل
                dataframe = dataframe.dropna(
                    how='all'
                )

                # حذف الأعمدة الفارغة بالكامل
                dataframe = dataframe.dropna(
                    axis=1,
                    how='all',
                )

                # نسخ DataFrame لمنع تعديل البيانات الأصلية
                dataframe = dataframe.copy()

                # تحويل أسماء الأعمدة إلى نصوص
                dataframe.columns = [
                    str(column)
                    for column in dataframe.columns
                ]

                rows_count = int(
                    dataframe.shape[0]
                )

                columns_count = int(
                    dataframe.shape[1]
                )

                columns = dataframe.columns.tolist()

                column_types = []

                for column in dataframe.columns:
                    column_types.append({
                        'name': column,
                        'type': str(
                            dataframe[column].dtype
                        ),
                    })

                missing_values = []

                sheet_missing_count = 0

                for column in dataframe.columns:
                    missing_count = int(
                        dataframe[column]
                        .isna()
                        .sum()
                    )

                    sheet_missing_count += missing_count

                    missing_values.append({
                        'column': column,
                        'count': missing_count,
                    })

                # معاينة أول 10 صفوف
                preview_dataframe = (
                    dataframe.head(10).copy()
                )

                preview_dataframe = (
                    preview_dataframe
                    .astype(object)
                    .where(
                        pd.notna(preview_dataframe),
                        'فارغ',
                    )
                )

                preview_rows = (
                    preview_dataframe.to_dict(
                        orient='records'
                    )
                )

                # تحديد الأعمدة الرقمية
                numeric_dataframe = (
                    dataframe.select_dtypes(
                        include='number'
                    )
                )

                numeric_statistics = []

                if not numeric_dataframe.empty:
                    statistics = (
                        numeric_dataframe
                        .describe()
                        .round(2)
                    )

                    for column in numeric_dataframe.columns:
                        count_value = safe_number(
                            statistics.loc[
                                'count',
                                column,
                            ]
                        )

                        mean_value = safe_number(
                            statistics.loc[
                                'mean',
                                column,
                            ]
                        )

                        std_value = safe_number(
                            statistics.loc[
                                'std',
                                column,
                            ]
                        )

                        min_value = safe_number(
                            statistics.loc[
                                'min',
                                column,
                            ]
                        )

                        max_value = safe_number(
                            statistics.loc[
                                'max',
                                column,
                            ]
                        )

                        numeric_statistics.append({
                            'column': column,
                            'count': count_value,
                            'mean': mean_value,
                            'std': std_value,
                            'min': min_value,
                            'max': max_value,
                        })

                        # بيانات الرسم البياني الرقمي
                        numeric_chart_labels.append(
                            f'{sheet_name} - {column}'
                        )

                        numeric_chart_means.append(
                            mean_value
                        )

                        numeric_chart_max_values.append(
                            max_value
                        )

                        numeric_chart_min_values.append(
                            min_value
                        )

                sheet_analysis = {
                    'name': sheet_name,
                    'rows_count': rows_count,
                    'columns_count': columns_count,
                    'missing_count': sheet_missing_count,
                    'numeric_columns_count': int(
                        numeric_dataframe.shape[1]
                    ),
                    'columns': columns,
                    'column_types': column_types,
                    'missing_values': missing_values,
                    'numeric_statistics': numeric_statistics,
                    'preview_rows': preview_rows,
                    'has_data': (
                        rows_count > 0
                        and columns_count > 0
                    ),
                }

                sheets_analysis.append(
                    sheet_analysis
                )

                total_rows += rows_count
                total_columns += columns_count
                total_missing_values += (
                    sheet_missing_count
                )
                total_numeric_columns += int(
                    numeric_dataframe.shape[1]
                )

                chart_sheet_names.append(
                    sheet_name
                )
                chart_rows.append(
                    rows_count
                )
                chart_columns.append(
                    columns_count
                )
                chart_missing_values.append(
                    sheet_missing_count
                )

            context.update({
                'analysis_complete': True,
                'file_name': uploaded_file.name,
                'sheets_count': len(
                    sheets_analysis
                ),
                'sheets_analysis': sheets_analysis,
                'total_rows': total_rows,
                'total_columns': total_columns,
                'total_missing_values': (
                    total_missing_values
                ),
                'total_numeric_columns': (
                    total_numeric_columns
                ),

                # بيانات داشبورد الأوراق
                'chart_sheet_names': (
                    chart_sheet_names
                ),
                'chart_rows': chart_rows,
                'chart_columns': chart_columns,
                'chart_missing_values': (
                    chart_missing_values
                ),

                # بيانات الرسوم الرقمية
                'numeric_chart_labels': (
                    numeric_chart_labels
                ),
                'numeric_chart_means': (
                    numeric_chart_means
                ),
                'numeric_chart_max_values': (
                    numeric_chart_max_values
                ),
                'numeric_chart_min_values': (
                    numeric_chart_min_values
                ),
            })

        except ImportError:
            context['error_message'] = (
                'مكتبة قراءة ملفات Excel غير مثبتة. '
                'ثبت openpyxl ثم أعد المحاولة.'
            )

        except ValueError:
            context['error_message'] = (
                'تعذر قراءة الملف. '
                'تأكد من أن الملف ملف Excel صالح.'
            )

        except Exception as error:
            context['error_message'] = (
                'حدث خطأ أثناء تحليل الملف: '
                f'{error}'
            )

    return render(
        request,
        'datasets-templates/dataset_home.html',
        context,
    )