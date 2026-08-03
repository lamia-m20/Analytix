import json
import logging
import os
import re
from typing import Annotated
from typing import Literal

from django.db import transaction
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import StringConstraints

from dashboards.models import Dashboard
from dashboards.models import DashboardWidget


logger = logging.getLogger(__name__)

MAX_ACTIONS = 10
MAX_COLORS = 10
ALLOWED_ACTIONS = {'add', 'update', 'delete'}
ALLOWED_CHART_TYPES = {'bar', 'line', 'pie'}
ALLOWED_AGGREGATIONS = {'sum', 'count', 'average'}
NUMERIC_TYPE_MARKERS = ('int', 'float', 'decimal', 'number')
HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')
HexColor = Annotated[
    str,
    StringConstraints(
        pattern=r'^#[0-9A-Fa-f]{6}$',
    ),
]


class DashboardAIError(Exception):
    """خطأ آمن يمكن عرضه للمستخدم."""


class DashboardAIUnavailableError(DashboardAIError):
    """خدمة OpenAI غير متاحة أو غير مهيأة."""


class DashboardPlanValidationError(DashboardAIError):
    """خطة التعديل غير صالحة للتنفيذ."""


class DashboardAction(BaseModel):
    model_config = ConfigDict(extra='ignore')

    action: Literal['add', 'update', 'delete']
    widget_id: int | None = None
    target_title: str = ''
    title: str = ''
    widget_type: Literal['chart', 'kpi', 'table'] = 'chart'
    chart_type: Literal['bar', 'line', 'pie'] | None = None
    sheet_name: str = ''
    x_column: str = ''
    y_column: str = ''
    aggregation: Literal['sum', 'count', 'average'] = 'count'
    colors: list[HexColor] = Field(
        default_factory=list,
        max_length=MAX_COLORS,
    )


class DashboardPlan(BaseModel):
    model_config = ConfigDict(extra='ignore')

    actions: list[DashboardAction]
    message: str = ''


def build_dashboard_metadata(dataset, dashboard):
    return {
        'sheets': [
            {
                'name': sheet.name,
                'columns': [
                    {
                        'name': column.name,
                        'type': column.data_type,
                    }
                    for column in sheet.columns.all()
                ],
            }
            for sheet in dataset.sheets.all()
        ],
        'widgets': [
            {
                'id': widget.pk,
                'title': widget.title,
                'widget_type': (
                    widget.settings or {}
                ).get('widget_type', 'chart'),
                'chart_type': widget.widget_type,
                'sheet_name': (
                    widget.settings or {}
                ).get('sheet_name', ''),
                'x_column': widget.x_column,
                'y_column': widget.y_column,
                'colors': (
                    widget.settings or {}
                ).get('colors', []),
            }
            for widget in dashboard.widgets.filter(
                is_visible=True
            )
        ],
    }


def request_dashboard_plan(*, user_request, metadata):
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        raise DashboardAIUnavailableError(
            'خدمة تعديل الداشبورد غير مهيأة حاليًا.'
        )

    try:
        from openai import APIConnectionError
        from openai import APIStatusError
        from openai import APITimeoutError
        from openai import OpenAI
        from openai import RateLimitError
    except ImportError as error:
        logger.exception('OpenAI SDK is not installed.')
        raise DashboardAIUnavailableError(
            'خدمة تعديل الداشبورد غير متاحة حاليًا.'
        ) from error

    payload = {
        'user_request': user_request,
        'excel_structure': metadata['sheets'],
        'current_widgets': metadata['widgets'],
    }
    instructions = (
        'أنت مخطط تعديلات آمن لداشبورد عربي. أعد JSON فقط وفق '
        'المخطط المحدد. العمليات المسموحة add وupdate وdelete، '
        'وأنواع المخططات bar وline وpie فقط. لا تُرجع كودًا أو SQL. '
        'استخدم معرفات العناصر المعطاة فقط ولا تخترع أوراقًا أو أعمدة. '
        'عند طلب تغيير القيم الفارغة من دائري إلى أعمدة، أعد update '
        'لكل عنصر مطابق نوعه pie واجعل chart_type=bar. '
        'عند طلب ألوان لكل الداشبورد، أعد update منفصلًا لكل عنصر حالي. '
        'حوّل أسماء الألوان العربية إلى Hex فقط: وردي #ec4899، '
        'أصفر #facc15، أزرق #3b82f6، أخضر #22c55e، '
        'أحمر #ef4444، بنفسجي #8b5cf6، برتقالي #f97316، '
        'رمادي #6b7280. لا تُرجع CSS أو JavaScript أو نص ألوان خام. '
        'الحد الأقصى 10 عمليات.'
    )

    try:
        client = OpenAI(
            api_key=api_key,
            timeout=20.0,
            max_retries=1,
        )
        response = client.responses.parse(
            model=os.getenv(
                'OPENAI_DASHBOARD_MODEL',
                'gpt-5.6',
            ),
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
            text_format=DashboardPlan,
        )
        plan = response.output_parsed
    except (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        APIStatusError,
    ) as error:
        logger.warning(
            'OpenAI dashboard request failed: %s',
            type(error).__name__,
        )
        raise DashboardAIUnavailableError(
            'تعذر الاتصال بخدمة تعديل الداشبورد حاليًا. حاول لاحقًا.'
        ) from error
    except Exception as error:
        logger.exception(
            'Unexpected OpenAI dashboard response failure.'
        )
        raise DashboardAIUnavailableError(
            'تعذر فهم طلب تعديل الداشبورد حاليًا.'
        ) from error

    if plan is None or not plan.actions:
        raise DashboardPlanValidationError(
            'لم يتم العثور على تعديل قابل للتنفيذ في طلبك.'
        )
    if len(plan.actions) > MAX_ACTIONS:
        raise DashboardPlanValidationError(
            'الطلب يحتوي على تعديلات كثيرة. قسّمه إلى طلبات أصغر.'
        )
    return plan


def _sheet_map(metadata):
    return {
        sheet['name']: {
            column['name']: column['type']
            for column in sheet['columns']
        }
        for sheet in metadata['sheets']
    }


def _is_numeric(data_type):
    normalized = data_type.lower()
    return any(
        marker in normalized
        for marker in NUMERIC_TYPE_MARKERS
    )


def _validate_add_action(action, sheets):
    if action.widget_type != 'chart':
        raise DashboardPlanValidationError(
            'يمكن إضافة المخططات فقط في هذه المرحلة.'
        )
    if action.chart_type not in ALLOWED_CHART_TYPES:
        raise DashboardPlanValidationError(
            'نوع المخطط المطلوب غير مسموح.'
        )
    if action.aggregation not in ALLOWED_AGGREGATIONS:
        raise DashboardPlanValidationError(
            'طريقة التجميع المطلوبة غير مسموحة.'
        )

    columns = sheets.get(action.sheet_name)
    if columns is None:
        raise DashboardPlanValidationError(
            'ورقة العمل المطلوبة غير موجودة.'
        )
    if (
        action.x_column not in columns
        or action.y_column not in columns
    ):
        raise DashboardPlanValidationError(
            'أحد الأعمدة المطلوبة غير موجود في ورقة العمل.'
        )
    if (
        action.aggregation in {'sum', 'average'}
        and not _is_numeric(columns[action.y_column])
    ):
        raise DashboardPlanValidationError(
            'التجميع المطلوب يحتاج إلى عمود قيم رقمي.'
        )


def _validate_colors(colors):
    if len(colors) > MAX_COLORS:
        raise DashboardPlanValidationError(
            'لا يمكن استخدام أكثر من 10 ألوان للمخطط الواحد.'
        )

    if any(
        not isinstance(color, str)
        or not HEX_COLOR_PATTERN.fullmatch(color)
        for color in colors
    ):
        raise DashboardPlanValidationError(
            'أحد ألوان المخطط غير صالح.'
        )

    return [
        color.lower()
        for color in colors
    ]


@transaction.atomic
def apply_dashboard_plan(
    *,
    dashboard,
    user,
    metadata,
    plan,
):
    if isinstance(plan, dict):
        try:
            plan = DashboardPlan.model_validate(plan)
        except Exception as error:
            raise DashboardPlanValidationError(
                'استجابة تعديل الداشبورد غير صالحة.'
            ) from error

    if not plan.actions or len(plan.actions) > MAX_ACTIONS:
        raise DashboardPlanValidationError(
            'عدد عمليات التعديل غير صالح.'
        )

    try:
        locked_dashboard = (
            Dashboard.objects
            .select_for_update()
            .get(
                pk=dashboard.pk,
                owner_id=user.pk,
            )
        )
    except Dashboard.DoesNotExist as error:
        raise DashboardPlanValidationError(
            'لوحة المعلومات المطلوبة غير موجودة.'
        ) from error

    sheets = _sheet_map(metadata)
    next_order = locked_dashboard.widgets.count()
    applied_count = 0

    for action in plan.actions:
        colors = _validate_colors(action.colors)

        if action.action == 'add':
            _validate_add_action(action, sheets)
            DashboardWidget.objects.create(
                dashboard=locked_dashboard,
                title=(
                    action.title.strip() or 'مخطط جديد'
                )[:255],
                widget_type=action.chart_type,
                x_column=action.x_column,
                y_column=action.y_column,
                aggregation=action.aggregation,
                display_order=next_order,
                settings={
                    'source': 'custom',
                    'widget_type': 'chart',
                    'chart_type': action.chart_type,
                    'sheet_name': action.sheet_name,
                    'colors': colors,
                },
            )
            next_order += 1
            applied_count += 1
            continue

        if not action.widget_id:
            raise DashboardPlanValidationError(
                'لم يتم تحديد عنصر الداشبورد المطلوب.'
            )

        widget = (
            DashboardWidget.objects
            .select_for_update()
            .filter(
                pk=action.widget_id,
                dashboard=locked_dashboard,
            )
            .first()
        )
        if widget is None:
            raise DashboardPlanValidationError(
                'عنصر الداشبورد المطلوب غير موجود أو لا تملك صلاحية تعديله.'
            )

        if action.action == 'delete':
            widget.delete()
            applied_count += 1
            continue

        update_fields = []
        if action.chart_type:
            widget.widget_type = action.chart_type
            widget.settings = {
                **(widget.settings or {}),
                'chart_type': action.chart_type,
            }
            update_fields.extend(['widget_type', 'settings'])
        if action.title.strip():
            widget.title = action.title.strip()[:255]
            update_fields.append('title')
        if colors:
            widget.settings = {
                **(widget.settings or {}),
                'colors': colors,
            }
            if 'settings' not in update_fields:
                update_fields.append('settings')
        if not update_fields:
            raise DashboardPlanValidationError(
                'لم يتضمن الطلب تغييرًا صالحًا للعنصر.'
            )

        widget.save(update_fields=list(set(update_fields)))
        applied_count += 1

    return applied_count
