from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.ai_assets.models import AiUseCase, RiskLevel
from apps.assessments.models import Assessment, AssessmentAnswer
from apps.compliance.models import Control, Risk
from apps.evidence.models import Evidence
from apps.organizations.models import Organization

from .models import DataQualityCheck, MetricDefinition, MetricSnapshot


METRIC_DEFINITIONS = [
    ("ai_use_cases.count", "AI use cases", "Total AI use cases by organization."),
    ("controls.count", "Controls", "Total controls by organization."),
    ("evidence.count", "Evidence", "Total evidence records by organization."),
    ("risks.low.count", "Low risks", "Total low severity risks by organization."),
    ("risks.medium.count", "Medium risks", "Total medium severity risks by organization."),
    ("risks.high.count", "High risks", "Total high severity risks by organization."),
    ("risks.critical.count", "Critical risks", "Total critical severity risks by organization."),
    ("risks.open.count", "Open risks", "Total open risks by organization."),
    ("risks.mitigating.count", "Mitigating risks", "Total mitigating risks by organization."),
    ("risks.accepted.count", "Accepted risks", "Total accepted risks by organization."),
    ("risks.closed.count", "Closed risks", "Total closed risks by organization."),
    ("assessments.draft.count", "Draft assessments", "Total draft assessments by organization."),
    ("assessments.in_progress.count", "In progress assessments", "Total in progress assessments by organization."),
    ("assessments.submitted.count", "Submitted assessments", "Total submitted assessments by organization."),
    ("assessments.archived.count", "Archived assessments", "Total archived assessments by organization."),
]


def run_data_quality_checks():
    executed_at = timezone.now()
    definitions = [
        _check_ai_use_cases_have_organization,
        _check_assessments_have_framework,
        _check_answers_have_questions,
        _check_risk_scales_are_valid,
        _check_evidence_has_location,
    ]
    return [definition(executed_at) for definition in definitions]


def generate_metric_snapshots(period_start=None, period_end=None, computed_at=None):
    computed_at = computed_at or timezone.now()
    period_start = period_start or computed_at.replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = period_end or period_start + timedelta(days=1)
    metric_definitions = _ensure_metric_definitions()
    snapshots = []

    for organization in Organization.objects.all():
        metric_values = _metric_values_for_organization(organization)
        for metric_key, metric_value in metric_values.items():
            snapshot, _created = MetricSnapshot.objects.update_or_create(
                organization=organization,
                metric_definition=metric_definitions[metric_key],
                period_start=period_start,
                period_end=period_end,
                defaults={
                    "metric_value": Decimal(metric_value),
                    "dimensions": {},
                    "computed_at": computed_at,
                },
            )
            snapshots.append(snapshot)

    return snapshots


def _ensure_metric_definitions():
    metric_definitions = {}
    for key, name, description in METRIC_DEFINITIONS:
        metric_definition, _created = MetricDefinition.objects.update_or_create(
            key=key,
            defaults={
                "name": name,
                "description": description,
                "value_type": MetricDefinition.ValueType.INTEGER,
                "status": MetricDefinition.Status.ACTIVE,
            },
        )
        metric_definitions[key] = metric_definition
    return metric_definitions


def _metric_values_for_organization(organization):
    risks = Risk.objects.filter(organization=organization)
    assessments = Assessment.objects.filter(organization=organization)
    values = {
        "ai_use_cases.count": AiUseCase.objects.filter(organization=organization).count(),
        "controls.count": Control.objects.filter(organization=organization).count(),
        "evidence.count": Evidence.objects.filter(organization=organization).count(),
    }

    for severity, _label in RiskLevel.choices:
        values[f"risks.{severity}.count"] = risks.filter(severity=severity).count()
    for status_value, _label in Risk.Status.choices:
        values[f"risks.{status_value}.count"] = risks.filter(status=status_value).count()
    for status_value, _label in Assessment.Status.choices:
        values[f"assessments.{status_value}.count"] = assessments.filter(status=status_value).count()

    return values


def _create_check(*, check_key, target_table, invalid_count, executed_at, result=None):
    status = DataQualityCheck.Status.PASSED if invalid_count == 0 else DataQualityCheck.Status.FAILED
    return DataQualityCheck.objects.create(
        check_key=check_key,
        target_table=target_table,
        status=status,
        result={"invalid_rows": invalid_count, **(result or {})},
        executed_at=executed_at,
    )


def _check_ai_use_cases_have_organization(executed_at):
    invalid_count = AiUseCase.objects.filter(organization__isnull=True).count()
    return _create_check(
        check_key="ai_use_case.organization.present",
        target_table="ai_assets_aiusecase",
        invalid_count=invalid_count,
        executed_at=executed_at,
    )


def _check_assessments_have_framework(executed_at):
    invalid_count = Assessment.objects.filter(framework__isnull=True).count()
    return _create_check(
        check_key="assessment.framework.present",
        target_table="assessments_assessment",
        invalid_count=invalid_count,
        executed_at=executed_at,
    )


def _check_answers_have_questions(executed_at):
    invalid_count = AssessmentAnswer.objects.filter(question__isnull=True).count()
    return _create_check(
        check_key="assessment_answer.question.present",
        target_table="assessments_assessmentanswer",
        invalid_count=invalid_count,
        executed_at=executed_at,
    )


def _check_risk_scales_are_valid(executed_at):
    invalid_count = Risk.objects.filter(likelihood__lt=1).count()
    invalid_count += Risk.objects.filter(likelihood__gt=5).count()
    invalid_count += Risk.objects.filter(impact__lt=1).count()
    invalid_count += Risk.objects.filter(impact__gt=5).count()
    return _create_check(
        check_key="risk.scale.valid",
        target_table="compliance_risk",
        invalid_count=invalid_count,
        executed_at=executed_at,
        result={"expected_range": "1..5"},
    )


def _check_evidence_has_location(executed_at):
    invalid_count = Evidence.objects.filter(file_path="", external_url="").count()
    return _create_check(
        check_key="evidence.location.present",
        target_table="evidence_evidence",
        invalid_count=invalid_count,
        executed_at=executed_at,
    )
