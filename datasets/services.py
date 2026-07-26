import pandas as pd

from django.db import transaction

from .models import DatasetColumn
from .models import DatasetSheet


@transaction.atomic
def create_dataset_structure(
    dataset,
    uploaded_file,
):
    """
    قراءة أسماء أوراق Excel وقراءة أول 200 صف
    فقط من كل ورقة، لتقليل استهلاك ذاكرة السيرفر.
    """

    uploaded_file.seek(0)

    workbook = pd.ExcelFile(
        uploaded_file
    )

    dataset.sheets.all().delete()

    for sheet_index, sheet_name in enumerate(
        workbook.sheet_names
    ):
        sample = workbook.parse(
            sheet_name=sheet_name,
            nrows=200,
        )

        sheet = DatasetSheet.objects.create(
            dataset=dataset,
            name=str(sheet_name),
            index=sheet_index,
            row_count=len(sample.index),
            column_count=len(sample.columns),
        )

        columns_to_create = []

        for position, column_name in enumerate(
            sample.columns
        ):
            series = sample[column_name]

            examples = [
                str(value)
                for value in (
                    series
                    .dropna()
                    .head(5)
                    .tolist()
                )
            ]

            columns_to_create.append(
                DatasetColumn(
                    sheet=sheet,
                    name=str(column_name),
                    position=position,
                    data_type=str(
                        series.dtype
                    ),
                    null_count=int(
                        series.isna().sum()
                    ),
                    unique_count=int(
                        series.nunique(
                            dropna=True
                        )
                    ),
                    sample_values=examples,
                )
            )

        DatasetColumn.objects.bulk_create(
            columns_to_create
        )

    dataset.status = 'ready'
    dataset.error_message = ''

    dataset.save(
        update_fields=[
            'status',
            'error_message',
            'updated_at',
        ],
    )