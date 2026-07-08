from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.assessments.models import (
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)


FRAMEWORK = {
    "code": "AIGOV",
    "name": "AI Governance Baseline",
    "version": "1.0",
    "status": AssessmentFramework.Status.PUBLISHED,
    "dimensions": [
        {
            "code": "governance",
            "name": "Governance",
            "description": "Accountability, ownership, and policy coverage for AI use.",
            "display_order": 1,
            "questions": [
                {
                    "code": "governance-001",
                    "text": "Does the organization maintain an inventory of AI tools and use cases?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
                },
                {
                    "code": "governance-002",
                    "text": "Are business owners assigned for production AI use cases?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "privacy",
            "name": "Privacy and Data Protection",
            "description": "Data classification and personal data handling in AI systems.",
            "display_order": 2,
            "questions": [
                {
                    "code": "privacy-001",
                    "text": "Are AI use cases classified by data sensitivity?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
                },
                {
                    "code": "privacy-002",
                    "text": "Are personal and sensitive data uses reviewed before production deployment?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "risk",
            "name": "Risk and Controls",
            "description": "Risk assessment, mitigation, controls, and evidence tracking.",
            "display_order": 3,
            "questions": [
                {
                    "code": "risk-001",
                    "text": "Are risks documented for high-impact AI use cases?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
                {
                    "code": "risk-002",
                    "text": "Are controls linked to risks and supported by evidence?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 2,
                },
            ],
        },
    ],
}


class Command(BaseCommand):
    help = "Seed baseline assessment frameworks, dimensions, and questions."

    @transaction.atomic
    def handle(self, *args, **options):
        framework, _ = AssessmentFramework.objects.update_or_create(
            code=FRAMEWORK["code"],
            version=FRAMEWORK["version"],
            defaults={
                "name": FRAMEWORK["name"],
                "status": FRAMEWORK["status"],
            },
        )

        dimension_count = 0
        question_count = 0
        for dimension_data in FRAMEWORK["dimensions"]:
            questions = dimension_data["questions"]
            dimension, _ = AssessmentDimension.objects.update_or_create(
                framework=framework,
                code=dimension_data["code"],
                defaults={
                    "name": dimension_data["name"],
                    "description": dimension_data["description"],
                    "display_order": dimension_data["display_order"],
                },
            )
            dimension_count += 1

            for question_data in questions:
                AssessmentQuestion.objects.update_or_create(
                    framework=framework,
                    code=question_data["code"],
                    defaults={
                        **question_data,
                        "dimension": dimension,
                        "is_required": True,
                    },
                )
                question_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {framework.code} v{framework.version}: "
                f"{dimension_count} dimensions, {question_count} questions."
            )
        )
