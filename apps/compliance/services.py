from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.ai_assets.models import RiskLevel
from apps.assessments.models import Assessment
from apps.audit.services import log_create_event
from apps.organizations.models import Membership

from .models import ActionItem, ActionPlan, Control, Risk, RiskAssessment, RiskControl


MITIGATION_THRESHOLD = Decimal("80.00")

DIMENSION_RULES = {
    "tooling": {
        "risk_title": "AI inventory gap",
        "control_codes": ["GOV-001"],
        "impact": 3,
        "action_items": [
            "List all AI tools currently used by the organization.",
            "Assign an owner for each AI tool and use case.",
            "Review unsupported or unapproved AI tools.",
        ],
    },
    "usage-area": {
        "risk_title": "Unclear AI ownership by business area",
        "control_codes": ["GOV-001"],
        "impact": 3,
        "action_items": [
            "Map AI use cases by business area.",
            "Assign business and technical owners.",
            "Validate responsibilities with area leaders.",
        ],
    },
    "purpose": {
        "risk_title": "Insufficient purpose documentation for AI use",
        "control_codes": ["GOV-002"],
        "impact": 3,
        "action_items": [
            "Document the purpose and expected outputs of each AI use case.",
            "Define allowed and restricted uses for each AI tool.",
            "Review use cases without clear business justification.",
        ],
    },
    "data-sharing": {
        "risk_title": "Sensitive data exposure in AI tools",
        "control_codes": ["PRIV-001", "SEC-001"],
        "impact": 5,
        "action_items": [
            "Classify data shared with AI tools by sensitivity.",
            "Define anonymization or minimization rules before AI use.",
            "Block sharing of credentials, secrets, and unnecessary personal data.",
        ],
    },
    "ai-decisions": {
        "risk_title": "Uncontrolled AI influence on business decisions",
        "control_codes": ["GOV-002", "HUM-001"],
        "impact": 5,
        "action_items": [
            "Identify decisions influenced by AI outputs.",
            "Define escalation rules for people-impacting decisions.",
            "Require documented human accountability before final decisions.",
        ],
    },
    "human-review": {
        "risk_title": "Missing human review for AI outputs",
        "control_codes": ["HUM-001"],
        "impact": 4,
        "action_items": [
            "Define which AI outputs require mandatory human review.",
            "Document review criteria for critical AI-assisted processes.",
            "Train reviewers on validation and escalation procedures.",
        ],
    },
    "governance": {
        "risk_title": "Weak AI governance practices",
        "control_codes": ["GOV-002", "TRN-001"],
        "impact": 4,
        "action_items": [
            "Create or update the corporate AI usage policy.",
            "Publish responsibilities for AI governance.",
            "Run periodic AI governance training.",
        ],
    },
    "security": {
        "risk_title": "Insufficient AI security controls",
        "control_codes": ["SEC-001"],
        "impact": 5,
        "action_items": [
            "Review access to AI tools and related repositories.",
            "Define incident handling for AI-related data exposure.",
            "Review vendor and tool security settings.",
        ],
    },
    "dependency": {
        "risk_title": "Operational dependency on AI tools",
        "control_codes": ["OPS-001"],
        "impact": 4,
        "action_items": [
            "Identify critical processes dependent on AI tools.",
            "Define manual fallback procedures.",
            "Test continuity for high-impact AI-assisted routines.",
        ],
    },
}


@transaction.atomic
def generate_mitigation_plan_from_assessment(assessment, actor_user):
    assessment = Assessment.objects.select_related("organization", "framework").get(pk=assessment.pk)
    if assessment.status != Assessment.Status.SUBMITTED:
        raise serializers.ValidationError({"assessment": "Assessment must be submitted before mitigation planning."})

    dimension_scores = assessment.maturity_scores.filter(dimension__isnull=False).select_related("dimension")
    if not dimension_scores.exists():
        raise serializers.ValidationError({"assessment": "Assessment has no maturity scores to evaluate."})

    actor_membership = _active_membership_for_user(actor_user, assessment.organization)
    generated_items = []
    for score in dimension_scores:
        if score.percentage >= MITIGATION_THRESHOLD:
            continue
        generated_items.append(_generate_dimension_plan(assessment, score, actor_membership, actor_user))

    return {
        "assessment": str(assessment.uuid),
        "organization": str(assessment.organization.uuid),
        "generated_count": len(generated_items),
        "items": generated_items,
    }


def derive_risk_severity(likelihood, impact):
    risk_score = int(likelihood) * int(impact)
    if risk_score >= 20:
        return RiskLevel.CRITICAL
    if risk_score >= 12:
        return RiskLevel.HIGH
    if risk_score >= 6:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _generate_dimension_plan(assessment, score, actor_membership, actor_user):
    organization = assessment.organization
    dimension = score.dimension
    rule = DIMENSION_RULES.get(dimension.code, _default_rule(dimension))
    likelihood = _likelihood_for_percentage(score.percentage)
    impact = rule["impact"]
    severity = derive_risk_severity(likelihood, impact)
    risk = _upsert_risk(
        assessment=assessment,
        dimension_code=dimension.code,
        rule=rule,
        likelihood=likelihood,
        impact=impact,
        severity=severity,
        actor_user=actor_user,
    )
    risk_assessment = _upsert_risk_assessment(
        risk=risk,
        actor_membership=actor_membership,
        likelihood=likelihood,
        impact=impact,
        severity=severity,
        score=score,
    )
    controls = _link_controls(risk, organization, rule["control_codes"])
    primary_control = controls[0] if controls else None
    action_plan = _upsert_action_plan(
        risk=risk,
        control=primary_control,
        assessment=assessment,
        dimension_code=dimension.code,
        score=score,
        actor_membership=actor_membership,
        actor_user=actor_user,
    )
    action_items = _upsert_action_items(
        action_plan=action_plan,
        risk=risk,
        control=primary_control,
        action_item_titles=rule["action_items"],
        actor_membership=actor_membership,
        actor_user=actor_user,
    )
    return _plan_payload(risk, risk_assessment, controls, action_plan, action_items)


def _upsert_risk(*, assessment, dimension_code, rule, likelihood, impact, severity, actor_user):
    title = f"{assessment.title}: {rule['risk_title']}"
    description = (
        f"Generated from assessment {assessment.uuid} for dimension '{dimension_code}'. "
        f"The current maturity level is below {MITIGATION_THRESHOLD}% and requires mitigation."
    )
    risk = Risk.objects.filter(organization=assessment.organization, title=title).first()
    if risk:
        risk.description = description
        risk.likelihood = likelihood
        risk.impact = impact
        risk.severity = severity
        risk.status = Risk.Status.OPEN
        risk.save(update_fields=["description", "likelihood", "impact", "severity", "status", "updated_at"])
        return risk
    risk = Risk.objects.create(
        organization=assessment.organization,
        title=title,
        description=description,
        likelihood=likelihood,
        impact=impact,
        severity=severity,
        status=Risk.Status.OPEN,
    )
    log_create_event(
        actor_user=actor_user,
        organization=assessment.organization,
        instance=risk,
        event_type="risk.created",
    )
    return risk


def _upsert_risk_assessment(*, risk, actor_membership, likelihood, impact, severity, score):
    rationale = (
        f"Generated from maturity score {score.percentage}% for dimension '{score.dimension.code}'."
    )
    risk_assessment = RiskAssessment.objects.filter(risk=risk).order_by("-created_at").first()
    if risk_assessment:
        risk_assessment.assessed_by = actor_membership
        risk_assessment.likelihood = likelihood
        risk_assessment.impact = impact
        risk_assessment.severity = severity
        risk_assessment.rationale = rationale
        risk_assessment.assessed_at = timezone.now()
        risk_assessment.save(
            update_fields=["assessed_by", "likelihood", "impact", "severity", "rationale", "assessed_at", "updated_at"]
        )
        return risk_assessment
    return RiskAssessment.objects.create(
        risk=risk,
        assessed_by=actor_membership,
        likelihood=likelihood,
        impact=impact,
        severity=severity,
        rationale=rationale,
        assessed_at=timezone.now(),
    )


def _link_controls(risk, organization, control_codes):
    controls = list(Control.objects.filter(organization=organization, code__in=control_codes))
    for control in controls:
        RiskControl.objects.get_or_create(risk=risk, control=control)
    return controls


def _upsert_action_plan(*, risk, control, assessment, dimension_code, score, actor_membership, actor_user):
    title = f"Mitigate {risk.title}"
    description = (
        f"Action plan generated from assessment {assessment.uuid} for dimension '{dimension_code}'. "
        f"Target: increase maturity from {score.percentage}% to at least {MITIGATION_THRESHOLD}%."
    )
    due_date = _due_date_for_severity(risk.severity)
    action_plan = ActionPlan.objects.filter(organization=assessment.organization, risk=risk, title=title).first()
    if action_plan:
        action_plan.control = control
        action_plan.description = description
        action_plan.status = ActionPlan.Status.OPEN
        action_plan.due_date = due_date
        action_plan.owner_membership = actor_membership
        action_plan.save(
            update_fields=["control", "description", "status", "due_date", "owner_membership", "updated_at"]
        )
        return action_plan
    action_plan = ActionPlan.objects.create(
        organization=assessment.organization,
        risk=risk,
        control=control,
        title=title,
        description=description,
        status=ActionPlan.Status.OPEN,
        due_date=due_date,
        owner_membership=actor_membership,
    )
    log_create_event(
        actor_user=actor_user,
        organization=assessment.organization,
        instance=action_plan,
        event_type="action_plan.created",
    )
    return action_plan


def _upsert_action_items(*, action_plan, risk, control, action_item_titles, actor_membership, actor_user):
    action_items = []
    for index, title in enumerate(action_item_titles, start=1):
        action_item = ActionItem.objects.filter(action_plan=action_plan, title=title).first()
        description = f"Step {index} for mitigating risk '{risk.title}'."
        if action_item:
            action_item.description = description
            action_item.risk = risk
            action_item.control = control
            action_item.owner_membership = actor_membership
            action_item.save(update_fields=["description", "risk", "control", "owner_membership", "updated_at"])
        else:
            action_item = ActionItem.objects.create(
                organization=action_plan.organization,
                action_plan=action_plan,
                risk=risk,
                control=control,
                title=title,
                description=description,
                status=ActionItem.Status.TODO,
                owner_membership=actor_membership,
            )
            log_create_event(
                actor_user=actor_user,
                organization=action_plan.organization,
                instance=action_item,
                event_type="action_item.created",
            )
        action_items.append(action_item)
    return action_items


def _plan_payload(risk, risk_assessment, controls, action_plan, action_items):
    return {
        "risk": {
            "uuid": str(risk.uuid),
            "title": risk.title,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "severity": risk.severity,
            "status": risk.status,
        },
        "risk_assessment": {
            "uuid": str(risk_assessment.uuid),
            "severity": risk_assessment.severity,
            "assessed_at": risk_assessment.assessed_at.isoformat(),
        },
        "controls": [
            {
                "uuid": str(control.uuid),
                "code": control.code,
                "title": control.title,
            }
            for control in controls
        ],
        "action_plan": {
            "uuid": str(action_plan.uuid),
            "title": action_plan.title,
            "status": action_plan.status,
            "due_date": action_plan.due_date.isoformat() if action_plan.due_date else None,
        },
        "action_items": [
            {
                "uuid": str(action_item.uuid),
                "title": action_item.title,
                "status": action_item.status,
            }
            for action_item in action_items
        ],
    }


def _likelihood_for_percentage(percentage):
    if percentage < Decimal("30.00"):
        return 5
    if percentage < Decimal("60.00"):
        return 4
    return 3


def _due_date_for_severity(severity):
    days_by_severity = {
        RiskLevel.CRITICAL: 30,
        RiskLevel.HIGH: 60,
        RiskLevel.MEDIUM: 90,
        RiskLevel.LOW: 120,
    }
    return timezone.localdate() + timedelta(days=days_by_severity[severity])


def _active_membership_for_user(user, organization):
    if not getattr(user, "is_authenticated", False):
        return None
    return Membership.objects.filter(
        user=user,
        organization=organization,
        status=Membership.Status.ACTIVE,
    ).first()


def _default_rule(dimension):
    return {
        "risk_title": f"{dimension.name} maturity gap",
        "control_codes": [],
        "impact": 3,
        "action_items": [
            f"Review weak practices in {dimension.name}.",
            f"Assign an owner for improving {dimension.name}.",
            f"Define evidence expected for {dimension.name}.",
        ],
    }
