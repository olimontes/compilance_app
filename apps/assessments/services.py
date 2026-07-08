from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_create_event

from .models import Assessment, AssessmentAnswer, AssessmentQuestion, MaturityScore, Recommendation


REQUIRED_DESCRIPTIVE_QUESTION_CODES = {"purpose-002", "data-sharing-002"}
YES_VALUES = {"yes", "sim", "true", "1", "y", "s"}
PARTIAL_VALUES = {"partial", "parcial", "partly", "sometimes"}
NO_VALUES = {"no", "nao", "não", "false", "0", "n"}


def is_required_descriptive_question(question):
    return question.code in REQUIRED_DESCRIPTIVE_QUESTION_CODES


def extract_text_answer(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "description", "answer"):
            raw_value = value.get(key)
            if isinstance(raw_value, str) and raw_value.strip():
                return raw_value.strip()
    return ""


@transaction.atomic
def submit_assessment(assessment, actor_user):
    assessment = Assessment.objects.select_for_update().get(pk=assessment.pk)
    _validate_required_answers(assessment)
    _recalculate_scores(assessment)
    _generate_recommendations(assessment)

    assessment.status = Assessment.Status.SUBMITTED
    assessment.submitted_at = timezone.now()
    assessment.save(update_fields=["status", "submitted_at", "updated_at"])
    log_create_event(
        actor_user=actor_user,
        organization=assessment.organization,
        instance=assessment,
        event_type="assessment.submitted",
    )
    return build_assessment_summary(assessment)


def build_assessment_summary(assessment):
    assessment = (
        Assessment.objects.select_related("organization", "framework")
        .prefetch_related("maturity_scores__dimension", "recommendations__dimension")
        .get(pk=assessment.pk)
    )
    overall = assessment.maturity_scores.filter(dimension__isnull=True).first()
    dimensions = [
        _dimension_summary(score)
        for score in assessment.maturity_scores.filter(dimension__isnull=False).select_related("dimension")
    ]
    recommendations = [
        {
            "uuid": str(recommendation.uuid),
            "dimension": recommendation.dimension.code if recommendation.dimension else None,
            "title": recommendation.title,
            "description": recommendation.description,
            "priority": recommendation.priority,
            "status": recommendation.status,
        }
        for recommendation in assessment.recommendations.select_related("dimension")
    ]

    return {
        "uuid": str(assessment.uuid),
        "title": assessment.title,
        "status": assessment.status,
        "submitted_at": assessment.submitted_at.isoformat() if assessment.submitted_at else None,
        "organization": str(assessment.organization.uuid),
        "framework": {
            "code": assessment.framework.code,
            "version": assessment.framework.version,
            "name": assessment.framework.name,
        },
        "overall_score": _score_payload(overall) if overall else None,
        "dimensions": dimensions,
        "recommendations": recommendations,
    }


def build_questionnaire(framework):
    dimensions = framework.dimensions.prefetch_related("questions").all()
    return {
        "framework": {
            "uuid": str(framework.uuid),
            "code": framework.code,
            "version": framework.version,
            "name": framework.name,
        },
        "dimensions": [
            {
                "uuid": str(dimension.uuid),
                "code": dimension.code,
                "name": dimension.name,
                "description": dimension.description,
                "display_order": dimension.display_order,
                "questions": [
                    {
                        "uuid": str(question.uuid),
                        "code": question.code,
                        "text": question.text,
                        "answer_type": question.answer_type,
                        "weight": str(question.weight),
                        "is_required": question.is_required,
                        "is_required_descriptive": is_required_descriptive_question(question),
                        "display_order": question.display_order,
                    }
                    for question in dimension.questions.all()
                ],
            }
            for dimension in dimensions
        ],
    }


def _validate_required_answers(assessment):
    questions = AssessmentQuestion.objects.filter(framework=assessment.framework)
    answers_by_question_id = {
        answer.question_id: answer
        for answer in AssessmentAnswer.objects.filter(assessment=assessment).select_related("question")
    }
    missing = []
    invalid_descriptions = []

    for question in questions:
        answer = answers_by_question_id.get(question.id)
        if question.is_required and answer is None:
            missing.append(question.code)
            continue
        if answer and is_required_descriptive_question(question) and not extract_text_answer(answer.value):
            invalid_descriptions.append(question.code)

    errors = {}
    if missing:
        errors["missing_required_questions"] = missing
    if invalid_descriptions:
        errors["invalid_descriptive_answers"] = invalid_descriptions
    if errors:
        from rest_framework import serializers

        raise serializers.ValidationError(errors)


def _recalculate_scores(assessment):
    now = timezone.now()
    questions = AssessmentQuestion.objects.filter(framework=assessment.framework).select_related("dimension")
    answers_by_question_id = {
        answer.question_id: answer
        for answer in AssessmentAnswer.objects.filter(assessment=assessment).select_related("question")
    }

    dimension_totals = {}
    for question in questions:
        score = _calculate_answer_score(question, answers_by_question_id.get(question.id))
        max_score = _quantize(question.weight)
        dimension_id = question.dimension_id
        if dimension_id not in dimension_totals:
            dimension_totals[dimension_id] = {
                "dimension": question.dimension,
                "score": Decimal("0.00"),
                "max_score": Decimal("0.00"),
            }
        dimension_totals[dimension_id]["score"] += score
        dimension_totals[dimension_id]["max_score"] += max_score

        answer = answers_by_question_id.get(question.id)
        if answer and answer.score != score:
            answer.score = score
            answer.save(update_fields=["score", "updated_at"])

    overall_score = Decimal("0.00")
    overall_max_score = Decimal("0.00")
    for item in dimension_totals.values():
        score = _quantize(item["score"])
        max_score = _quantize(item["max_score"])
        overall_score += score
        overall_max_score += max_score
        MaturityScore.objects.update_or_create(
            assessment=assessment,
            dimension=item["dimension"],
            defaults={
                "score": score,
                "max_score": max_score,
                "percentage": _percentage(score, max_score),
                "computed_at": now,
            },
        )

    MaturityScore.objects.update_or_create(
        assessment=assessment,
        dimension=None,
        defaults={
            "score": _quantize(overall_score),
            "max_score": _quantize(overall_max_score),
            "percentage": _percentage(overall_score, overall_max_score),
            "computed_at": now,
        },
    )


def _generate_recommendations(assessment):
    for score in assessment.maturity_scores.filter(dimension__isnull=False).select_related("dimension"):
        if score.percentage >= Decimal("80.00"):
            continue
        priority = _priority_for_percentage(score.percentage)
        title = f"Improve {score.dimension.name}"
        description = (
            f"The dimension '{score.dimension.name}' reached {score.percentage}% maturity. "
            "Review the weak controls, assign an owner, and create action items to reduce AI governance risk."
        )
        _upsert_recommendation(
            assessment=assessment,
            dimension=score.dimension,
            title=title,
            description=description,
            priority=priority,
        )


def _calculate_answer_score(question, answer):
    if answer is None:
        return Decimal("0.00")
    explicit_score = _explicit_score(answer.value)
    if explicit_score is not None:
        return _clamp_score(explicit_score, question.weight)
    if question.answer_type == AssessmentQuestion.AnswerType.BOOLEAN:
        return _boolean_score(answer.value, question.weight)
    if question.answer_type == AssessmentQuestion.AnswerType.CHOICE:
        return _choice_score(answer.value, question.weight)
    return Decimal("0.00")


def _explicit_score(value):
    if not isinstance(value, dict) or "score" not in value:
        return None
    try:
        return Decimal(str(value["score"]))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _boolean_score(value, weight):
    raw_value = value.get("answer") if isinstance(value, dict) else value
    if isinstance(raw_value, bool):
        return _quantize(weight if raw_value else Decimal("0.00"))
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in YES_VALUES:
            return _quantize(weight)
        if normalized in NO_VALUES:
            return Decimal("0.00")
    return Decimal("0.00")


def _choice_score(value, weight):
    raw_value = value.get("answer") if isinstance(value, dict) else value
    if not isinstance(raw_value, str):
        return Decimal("0.00")
    normalized = raw_value.strip().lower()
    if normalized in YES_VALUES:
        return _quantize(weight)
    if normalized in PARTIAL_VALUES:
        return _quantize(Decimal(weight) / Decimal("2"))
    if normalized in NO_VALUES:
        return Decimal("0.00")
    return Decimal("0.00")


def _clamp_score(score, max_score):
    score = _quantize(score)
    max_score = _quantize(max_score)
    if score < Decimal("0.00"):
        return Decimal("0.00")
    if score > max_score:
        return max_score
    return score


def _percentage(score, max_score):
    score = Decimal(score)
    max_score = Decimal(max_score)
    if max_score == Decimal("0.00"):
        return Decimal("100.00")
    return _quantize((score / max_score) * Decimal("100"))


def _priority_for_percentage(percentage):
    if percentage < Decimal("30.00"):
        return Recommendation.Priority.CRITICAL
    if percentage < Decimal("60.00"):
        return Recommendation.Priority.HIGH
    return Recommendation.Priority.MEDIUM


def _upsert_recommendation(*, assessment, dimension, title, description, priority):
    recommendation = Recommendation.objects.filter(
        assessment=assessment,
        dimension=dimension,
        title=title,
    ).first()
    if recommendation:
        recommendation.description = description
        recommendation.priority = priority
        recommendation.status = Recommendation.Status.OPEN
        recommendation.save(update_fields=["description", "priority", "status", "updated_at"])
        return recommendation
    return Recommendation.objects.create(
        assessment=assessment,
        dimension=dimension,
        title=title,
        description=description,
        priority=priority,
        status=Recommendation.Status.OPEN,
    )


def _dimension_summary(score):
    payload = _score_payload(score)
    payload["dimension"] = {
        "uuid": str(score.dimension.uuid),
        "code": score.dimension.code,
        "name": score.dimension.name,
    }
    return payload


def _score_payload(score):
    return {
        "score": str(score.score),
        "max_score": str(score.max_score),
        "percentage": str(score.percentage),
        "computed_at": score.computed_at.isoformat(),
    }


def _quantize(value):
    return Decimal(value).quantize(Decimal("0.01"))
