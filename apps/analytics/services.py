from django.utils import timezone

from apps.ai_assets.models import AiUseCase
from apps.assessments.models import Assessment, AssessmentAnswer
from apps.compliance.models import Risk
from apps.evidence.models import Evidence

from .models import DataQualityCheck


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
