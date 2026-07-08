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


DIMENSION_ENRICHMENT = {
    "tooling": {
        "objective": "Create a reliable inventory of AI tools and owners.",
        "justification": "Unknown AI tools make it difficult to apply policy, security, privacy, and vendor controls.",
        "expected_benefits": [
            "Clear accountability for AI tools.",
            "Lower chance of unsupported or unapproved AI use.",
        ],
        "impacted_areas": ["AI governance", "IT", "Business areas"],
        "success_indicators": [
            "All AI tools have an owner and business purpose recorded.",
            "Unapproved AI tools are reviewed or removed from active use.",
        ],
        "expected_evidence": [
            "Updated AI tool inventory.",
            "Approval or remediation record for each reviewed tool.",
        ],
        "consequences": {
            "legal": "Difficulty proving that AI tools are governed and used under approved policies.",
            "financial": "Unexpected vendor spend, remediation costs, or losses from uncontrolled tools.",
            "operational": "Teams may depend on tools that are unsupported, duplicated, or unavailable.",
            "reputational": "Stakeholders may lose confidence in the organization's AI governance discipline.",
        },
    },
    "usage-area": {
        "objective": "Clarify ownership and accountability by business area.",
        "justification": "AI use without area ownership creates gaps in approvals, controls, and escalation paths.",
        "expected_benefits": [
            "Defined business and technical accountability.",
            "Better prioritization of controls by area impact.",
        ],
        "impacted_areas": ["Business areas", "AI governance", "Risk and compliance"],
        "success_indicators": [
            "Each mapped AI use case has a business owner and technical owner.",
            "Area leaders validate responsibilities for high-impact AI use cases.",
        ],
        "expected_evidence": [
            "Ownership matrix by area and AI use case.",
            "Recorded validation from area leaders.",
        ],
        "consequences": {
            "legal": "Responsibility for policy adherence may be unclear during audits or disputes.",
            "financial": "Duplicated initiatives and unmanaged remediation can increase governance cost.",
            "operational": "Incidents and decisions may lack a clear escalation owner.",
            "reputational": "Internal users may perceive AI governance as inconsistent or arbitrary.",
        },
    },
    "purpose": {
        "objective": "Document approved AI purposes and usage boundaries.",
        "justification": "Poorly defined purpose increases the chance of misuse, scope creep, and weak accountability.",
        "expected_benefits": [
            "Clear business justification for each AI use case.",
            "Reduced misuse outside approved boundaries.",
        ],
        "impacted_areas": ["AI governance", "Legal", "Business areas"],
        "success_indicators": [
            "All active AI use cases have a documented purpose and allowed uses.",
            "Use cases without business justification are remediated or retired.",
        ],
        "expected_evidence": [
            "Purpose documentation for AI use cases.",
            "Approved usage policy or restricted-use register.",
        ],
        "consequences": {
            "legal": "AI processing may be hard to justify against policy, contract, or privacy obligations.",
            "financial": "Low-value or noncompliant use cases may continue consuming budget.",
            "operational": "Teams may apply AI outputs to decisions outside the intended scope.",
            "reputational": "Customers and employees may question why AI is being used in sensitive workflows.",
        },
    },
    "data-sharing": {
        "objective": "Control sensitive and personal data shared with AI tools.",
        "justification": "Uncontrolled data sharing can expose personal data, confidential information, or secrets.",
        "expected_benefits": [
            "Reduced privacy and confidentiality exposure.",
            "Clear data minimization and anonymization practices.",
        ],
        "impacted_areas": ["Privacy", "Security", "Legal", "Business areas"],
        "success_indicators": [
            "AI data sharing rules are approved and communicated.",
            "Sensitive data sharing is blocked, minimized, or anonymized before AI use.",
        ],
        "expected_evidence": [
            "Data classification and sharing policy for AI tools.",
            "Evidence of anonymization, blocking rules, or approved exceptions.",
        ],
        "consequences": {
            "legal": "Potential privacy, contractual, or confidentiality noncompliance.",
            "financial": "Possible fines, breach response cost, legal cost, or customer compensation.",
            "operational": "AI workflows may need to be suspended until data handling is remediated.",
            "reputational": "Data exposure can damage trust with customers, employees, and partners.",
        },
    },
    "ai-decisions": {
        "objective": "Limit uncontrolled AI influence on business decisions.",
        "justification": "AI-assisted decisions need accountability, escalation, and safeguards for impacted people.",
        "expected_benefits": [
            "Clear human accountability for AI-assisted decisions.",
            "Reduced risk of unfair or unsupported decision outcomes.",
        ],
        "impacted_areas": ["Legal", "Risk and compliance", "Business operations"],
        "success_indicators": [
            "Decisions influenced by AI are mapped and classified by impact.",
            "High-impact decisions require documented human accountability.",
        ],
        "expected_evidence": [
            "Decision inventory with AI influence level.",
            "Escalation and approval records for high-impact decisions.",
        ],
        "consequences": {
            "legal": "Affected parties may challenge decisions if accountability and rationale are unclear.",
            "financial": "Disputes, remediation, or compensation may arise from unsupported decisions.",
            "operational": "Decision workflows may become inconsistent across teams.",
            "reputational": "Perceived opaque or unfair AI use can damage institutional trust.",
        },
    },
    "human-review": {
        "objective": "Define mandatory human review for critical AI outputs.",
        "justification": "Human review reduces the impact of inaccurate, biased, or incomplete AI outputs.",
        "expected_benefits": [
            "Higher reliability for AI-assisted workflows.",
            "Clear review criteria for critical outputs.",
        ],
        "impacted_areas": ["Operations", "Risk and compliance", "Training"],
        "success_indicators": [
            "Critical AI outputs have documented review criteria.",
            "Reviewers complete training and record review outcomes.",
        ],
        "expected_evidence": [
            "Human review procedure and criteria.",
            "Review logs or approval records for sampled outputs.",
        ],
        "consequences": {
            "legal": "Unreviewed AI outputs may support decisions that are hard to defend.",
            "financial": "Errors may cause rework, customer impact, or remediation cost.",
            "operational": "Teams may rely on incorrect outputs without escalation.",
            "reputational": "Visible AI mistakes can reduce confidence in the organization's AI program.",
        },
    },
    "governance": {
        "objective": "Strengthen AI governance policy, roles, and training.",
        "justification": "Weak governance makes AI controls inconsistent and difficult to audit.",
        "expected_benefits": [
            "Consistent rules for responsible AI use.",
            "Better preparedness for audits and internal reviews.",
        ],
        "impacted_areas": ["AI governance", "Legal", "Risk and compliance", "Training"],
        "success_indicators": [
            "AI usage policy is approved and published.",
            "Relevant users complete AI governance training.",
        ],
        "expected_evidence": [
            "Approved AI policy and governance roles.",
            "Training completion report.",
        ],
        "consequences": {
            "legal": "The organization may lack evidence of reasonable governance practices.",
            "financial": "Remediation may become reactive and more expensive.",
            "operational": "Teams may apply different AI rules across similar workflows.",
            "reputational": "A weak governance posture can undermine confidence from clients and partners.",
        },
    },
    "security": {
        "objective": "Apply security controls to AI tools, access, and vendors.",
        "justification": "AI tools can expand the attack surface through access, prompts, integrations, and vendors.",
        "expected_benefits": [
            "Reduced likelihood of AI-related security incidents.",
            "Clear response path for AI data exposure or misuse.",
        ],
        "impacted_areas": ["Security", "IT", "Vendor management", "Operations"],
        "success_indicators": [
            "AI tools have access controls and security settings reviewed.",
            "AI-related incident handling is documented and tested.",
        ],
        "expected_evidence": [
            "Security review records for AI tools and vendors.",
            "Incident handling playbook for AI-related events.",
        ],
        "consequences": {
            "legal": "Security gaps may trigger contractual, regulatory, or notification obligations.",
            "financial": "Incidents can create investigation, recovery, downtime, and legal costs.",
            "operational": "Compromised tools or integrations may interrupt critical workflows.",
            "reputational": "Security failures around AI can weaken market and customer confidence.",
        },
    },
    "dependency": {
        "objective": "Reduce operational dependency risk for AI-assisted processes.",
        "justification": "Critical AI dependency without fallback can interrupt operations when tools fail or change.",
        "expected_benefits": [
            "Continuity for high-impact AI-assisted routines.",
            "Clear fallback procedures for tool outages or degradation.",
        ],
        "impacted_areas": ["Operations", "IT", "Business continuity"],
        "success_indicators": [
            "Critical AI dependencies are mapped and rated.",
            "Fallback procedures are tested for high-impact routines.",
        ],
        "expected_evidence": [
            "AI dependency register by process criticality.",
            "Business continuity test records or fallback procedures.",
        ],
        "consequences": {
            "legal": "Service failures may affect contractual obligations or regulated processes.",
            "financial": "Downtime can cause productivity loss, service credits, or emergency remediation cost.",
            "operational": "Teams may be unable to complete critical work without AI tools.",
            "reputational": "Visible disruption can make AI adoption look fragile or poorly managed.",
        },
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


def build_executive_report_from_assessment(assessment):
    assessment = Assessment.objects.select_related("organization", "framework").get(pk=assessment.pk)
    if assessment.status != Assessment.Status.SUBMITTED:
        raise serializers.ValidationError({"assessment": "Assessment must be submitted before executive report."})

    dimension_scores = list(
        assessment.maturity_scores.filter(dimension__isnull=False).select_related("dimension")
    )
    if not dimension_scores:
        raise serializers.ValidationError({"assessment": "Assessment has no maturity scores to report."})

    overall_score = assessment.maturity_scores.filter(dimension__isnull=True).first()
    weak_contexts = [
        _executive_context(assessment, score)
        for score in dimension_scores
        if score.percentage < MITIGATION_THRESHOLD
    ]

    return {
        "assessment": {
            "uuid": str(assessment.uuid),
            "title": assessment.title,
            "status": assessment.status,
            "submitted_at": assessment.submitted_at.isoformat() if assessment.submitted_at else None,
        },
        "organization": {
            "uuid": str(assessment.organization.uuid),
            "name": assessment.organization.name,
        },
        "framework": {
            "code": assessment.framework.code,
            "version": assessment.framework.version,
            "name": assessment.framework.name,
        },
        "generated_at": timezone.now().isoformat(),
        "executive_summary": _executive_summary(overall_score, weak_contexts),
        "identified_risks": [_executive_risk_payload(context) for context in weak_contexts],
        "mitigation_plan": [_executive_action_plan_payload(context) for context in weak_contexts],
        "recommended_next_steps": _recommended_next_steps(weak_contexts),
    }


def _generate_dimension_plan(assessment, score, actor_membership, actor_user):
    organization = assessment.organization
    dimension = score.dimension
    rule = DIMENSION_RULES.get(dimension.code, _default_rule(dimension))
    enrichment = _enrichment_for_dimension(dimension)
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
        enrichment=enrichment,
        actor_membership=actor_membership,
        actor_user=actor_user,
    )
    action_items = _upsert_action_items(
        action_plan=action_plan,
        risk=risk,
        control=primary_control,
        action_item_titles=rule["action_items"],
        enrichment=enrichment,
        actor_membership=actor_membership,
        actor_user=actor_user,
    )
    return _plan_payload(
        risk=risk,
        risk_assessment=risk_assessment,
        controls=controls,
        action_plan=action_plan,
        action_items=action_items,
        dimension=dimension,
        score=score,
        enrichment=enrichment,
    )


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


def _upsert_action_plan(
    *,
    risk,
    control,
    assessment,
    dimension_code,
    score,
    enrichment,
    actor_membership,
    actor_user,
):
    title = f"Mitigate {risk.title}"
    due_date = _due_date_for_severity(risk.severity)
    description = _action_plan_description(
        assessment=assessment,
        dimension_code=dimension_code,
        score=score,
        enrichment=enrichment,
        severity=risk.severity,
        due_date=due_date,
    )
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


def _upsert_action_items(
    *,
    action_plan,
    risk,
    control,
    action_item_titles,
    enrichment,
    actor_membership,
    actor_user,
):
    action_items = []
    for index, title in enumerate(action_item_titles, start=1):
        action_item = ActionItem.objects.filter(action_plan=action_plan, title=title).first()
        description = _action_item_description(index, title, risk, enrichment)
        if action_item:
            action_item.description = description
            action_item.risk = risk
            action_item.control = control
            action_item.due_date = action_plan.due_date
            action_item.owner_membership = actor_membership
            action_item.save(
                update_fields=[
                    "description",
                    "risk",
                    "control",
                    "due_date",
                    "owner_membership",
                    "updated_at",
                ]
            )
        else:
            action_item = ActionItem.objects.create(
                organization=action_plan.organization,
                action_plan=action_plan,
                risk=risk,
                control=control,
                title=title,
                description=description,
                status=ActionItem.Status.TODO,
                due_date=action_plan.due_date,
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


def _plan_payload(*, risk, risk_assessment, controls, action_plan, action_items, dimension, score, enrichment):
    return {
        "risk": {
            "uuid": str(risk.uuid),
            "title": risk.title,
            "dimension": {
                "uuid": str(dimension.uuid),
                "code": dimension.code,
                "name": dimension.name,
            },
            "maturity_percentage": str(score.percentage),
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "severity": risk.severity,
            "status": risk.status,
            "consequences": enrichment["consequences"],
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
            "objective": enrichment["objective"],
            "justification": enrichment["justification"],
            "expected_benefits": enrichment["expected_benefits"],
            "complexity": _complexity_for_severity(risk.severity),
            "impacted_areas": enrichment["impacted_areas"],
            "success_indicators": enrichment["success_indicators"],
            "expected_evidence": enrichment["expected_evidence"],
        },
        "action_items": [
            {
                "uuid": str(action_item.uuid),
                "title": action_item.title,
                "status": action_item.status,
                "due_date": action_item.due_date.isoformat() if action_item.due_date else None,
                "success_indicators": enrichment["success_indicators"],
                "expected_evidence": enrichment["expected_evidence"],
            }
            for action_item in action_items
        ],
    }


def _executive_context(assessment, score):
    dimension = score.dimension
    rule = DIMENSION_RULES.get(dimension.code, _default_rule(dimension))
    enrichment = _enrichment_for_dimension(dimension)
    likelihood = _likelihood_for_percentage(score.percentage)
    impact = rule["impact"]
    severity = derive_risk_severity(likelihood, impact)
    risk = _risk_for_assessment(assessment, rule)
    controls = _controls_for_report(assessment, risk, rule)
    action_plan = _action_plan_for_report(risk)
    action_items = list(action_plan.items.all()) if action_plan else []
    due_date = action_plan.due_date if action_plan else _due_date_for_severity(severity)

    return {
        "assessment": assessment,
        "score": score,
        "dimension": dimension,
        "rule": rule,
        "enrichment": enrichment,
        "likelihood": likelihood,
        "impact": impact,
        "severity": severity,
        "risk": risk,
        "controls": controls,
        "action_plan": action_plan,
        "action_items": action_items,
        "due_date": due_date,
    }


def _executive_summary(overall_score, contexts):
    sorted_contexts = sorted(contexts, key=lambda context: context["score"].percentage)
    priority_risk_count = sum(
        1
        for context in contexts
        if context["severity"] in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    )
    return {
        "headline": _executive_headline(overall_score, contexts),
        "overall_score": _maturity_score_payload(overall_score) if overall_score else None,
        "maturity_level": _maturity_level(overall_score.percentage) if overall_score else "unknown",
        "identified_risk_count": len(contexts),
        "priority_risk_count": priority_risk_count,
        "recommended_focus": [
            {
                "dimension": context["dimension"].code,
                "name": context["dimension"].name,
                "maturity_percentage": str(context["score"].percentage),
                "severity": context["severity"],
            }
            for context in sorted_contexts[:3]
        ],
    }


def _executive_risk_payload(context):
    risk = context["risk"]
    return {
        "uuid": str(risk.uuid) if risk else None,
        "title": risk.title if risk else _generated_risk_title(context["assessment"], context["rule"]),
        "dimension": _dimension_payload(context["dimension"]),
        "maturity_percentage": str(context["score"].percentage),
        "likelihood": risk.likelihood if risk else context["likelihood"],
        "impact": risk.impact if risk else context["impact"],
        "severity": risk.severity if risk else context["severity"],
        "status": risk.status if risk else "identified",
        "controls": [_control_payload(control) for control in context["controls"]],
        "consequences": context["enrichment"]["consequences"],
    }


def _executive_action_plan_payload(context):
    action_plan = context["action_plan"]
    enrichment = context["enrichment"]
    return {
        "uuid": str(action_plan.uuid) if action_plan else None,
        "title": action_plan.title if action_plan else f"Mitigate {_generated_risk_title(context['assessment'], context['rule'])}",
        "dimension": _dimension_payload(context["dimension"]),
        "status": action_plan.status if action_plan else "not_created",
        "due_date": _date_iso(action_plan.due_date if action_plan else None),
        "suggested_deadline": _date_iso(context["due_date"]),
        "objective": enrichment["objective"],
        "justification": enrichment["justification"],
        "expected_benefits": enrichment["expected_benefits"],
        "complexity": _complexity_for_severity(context["severity"]),
        "impacted_areas": enrichment["impacted_areas"],
        "success_indicators": enrichment["success_indicators"],
        "expected_evidence": enrichment["expected_evidence"],
        "items": _executive_action_item_payloads(context),
    }


def _executive_action_item_payloads(context):
    enrichment = context["enrichment"]
    if context["action_items"]:
        return [
            {
                "uuid": str(action_item.uuid),
                "title": action_item.title,
                "status": action_item.status,
                "due_date": _date_iso(action_item.due_date),
                "success_indicators": enrichment["success_indicators"],
                "expected_evidence": enrichment["expected_evidence"],
            }
            for action_item in context["action_items"]
        ]
    return [
        {
            "uuid": None,
            "title": title,
            "status": "not_created",
            "due_date": None,
            "success_indicators": enrichment["success_indicators"],
            "expected_evidence": enrichment["expected_evidence"],
        }
        for title in context["rule"]["action_items"]
    ]


def _recommended_next_steps(contexts):
    if not contexts:
        return [
            "Maintain periodic reassessment and evidence review.",
            "Keep AI inventory, policies, and control evidence current.",
        ]
    return [
        "Review the priority risks with accountable business and technical owners.",
        "Generate or update mitigation plans and assign due dates for each weak dimension.",
        "Collect the expected evidence before the next maturity reassessment.",
    ]


def _risk_for_assessment(assessment, rule):
    return Risk.objects.filter(
        organization=assessment.organization,
        title=_generated_risk_title(assessment, rule),
        description__contains=str(assessment.uuid),
    ).first()


def _controls_for_report(assessment, risk, rule):
    controls = list(risk.controls.all()) if risk else []
    if controls:
        return controls
    return list(Control.objects.filter(organization=assessment.organization, code__in=rule["control_codes"]))


def _action_plan_for_report(risk):
    if not risk:
        return None
    return risk.action_plans.prefetch_related("items").order_by("due_date", "created_at").first()


def _generated_risk_title(assessment, rule):
    return f"{assessment.title}: {rule['risk_title']}"


def _executive_headline(overall_score, contexts):
    if not overall_score:
        return "Assessment submitted, but the overall maturity score is unavailable."
    if not contexts:
        return "AI governance maturity is above the mitigation threshold across assessed dimensions."
    maturity_level = _maturity_level(overall_score.percentage)
    return (
        f"AI governance maturity is {maturity_level} with "
        f"{len(contexts)} dimension(s) requiring mitigation."
    )


def _maturity_level(percentage):
    if percentage < Decimal("30.00"):
        return "critical"
    if percentage < Decimal("60.00"):
        return "low"
    if percentage < Decimal("80.00"):
        return "moderate"
    return "strong"


def _maturity_score_payload(score):
    return {
        "score": str(score.score),
        "max_score": str(score.max_score),
        "percentage": str(score.percentage),
        "computed_at": score.computed_at.isoformat(),
    }


def _dimension_payload(dimension):
    return {
        "uuid": str(dimension.uuid),
        "code": dimension.code,
        "name": dimension.name,
    }


def _control_payload(control):
    return {
        "uuid": str(control.uuid),
        "code": control.code,
        "title": control.title,
    }


def _action_plan_description(*, assessment, dimension_code, score, enrichment, severity, due_date):
    return "\n".join(
        [
            f"Action plan generated from assessment {assessment.uuid} for dimension '{dimension_code}'.",
            f"Target: increase maturity from {score.percentage}% to at least {MITIGATION_THRESHOLD}%.",
            f"Objective: {enrichment['objective']}",
            f"Justification: {enrichment['justification']}",
            f"Expected benefits: {_join_values(enrichment['expected_benefits'])}",
            f"Complexity: {_complexity_for_severity(severity)}",
            f"Suggested deadline: {_date_iso(due_date)}",
            f"Impacted areas: {_join_values(enrichment['impacted_areas'])}",
            f"Success indicators: {_join_values(enrichment['success_indicators'])}",
            f"Expected evidence: {_join_values(enrichment['expected_evidence'])}",
        ]
    )


def _action_item_description(index, title, risk, enrichment):
    return "\n".join(
        [
            f"Step {index}: {title}",
            f"Mitigates risk: {risk.title}",
            f"Objective: {enrichment['objective']}",
            f"Expected benefits: {_join_values(enrichment['expected_benefits'])}",
            f"Success indicators: {_join_values(enrichment['success_indicators'])}",
            f"Expected evidence: {_join_values(enrichment['expected_evidence'])}",
        ]
    )


def _enrichment_for_dimension(dimension):
    enrichment = _default_enrichment(dimension)
    enrichment.update(DIMENSION_ENRICHMENT.get(dimension.code, {}))
    return enrichment


def _default_enrichment(dimension):
    return {
        "objective": f"Reduce the AI governance gap in {dimension.name}.",
        "justification": (
            f"The assessment shows {dimension.name} maturity below the "
            f"{MITIGATION_THRESHOLD}% mitigation threshold."
        ),
        "expected_benefits": [
            "Clear ownership of mitigation work.",
            "Evidence that the weak governance area is being remediated.",
        ],
        "impacted_areas": ["AI governance", "Risk and compliance"],
        "success_indicators": [
            f"{dimension.name} maturity reaches at least {MITIGATION_THRESHOLD}% in the next assessment.",
            "All mitigation action items are completed or formally accepted.",
        ],
        "expected_evidence": [
            "Documented owner, due date, and remediation decision.",
            "Updated control evidence linked to the relevant AI governance area.",
        ],
        "consequences": {
            "legal": "The organization may lack evidence that the AI risk is governed.",
            "financial": "Reactive remediation may increase cost if the risk materializes.",
            "operational": "Teams may continue using AI without a reliable control process.",
            "reputational": "Weak governance can reduce trust in the organization's AI practices.",
        },
    }


def _complexity_for_severity(severity):
    if severity in {RiskLevel.CRITICAL, RiskLevel.HIGH}:
        return "high"
    if severity == RiskLevel.MEDIUM:
        return "medium"
    return "low"


def _join_values(values):
    return "; ".join(values)


def _date_iso(value):
    return value.isoformat() if value else None


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
