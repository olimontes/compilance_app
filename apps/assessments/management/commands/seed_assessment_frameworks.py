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
            "code": "tooling",
            "name": "Ferramenta utilizada",
            "description": "Inventory and formal identification of AI tools used by the organization.",
            "display_order": 1,
            "questions": [
                {
                    "code": "tooling-001",
                    "text": "Does the organization maintain an inventory of AI tools and use cases?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
                },
                {
                    "code": "tooling-002",
                    "text": "Which AI tools are currently used by the organization?",
                    "answer_type": AssessmentQuestion.AnswerType.TEXT,
                    "weight": Decimal("0.00"),
                    "is_required": False,
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "usage-area",
            "name": "Area de utilizacao",
            "description": "Business areas, owners, and organizational context for AI use.",
            "display_order": 2,
            "questions": [
                {
                    "code": "usage-area-001",
                    "text": "Are the business areas and responsible owners identified for AI use cases?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
                },
                {
                    "code": "usage-area-002",
                    "text": "Describe which areas use AI and who is responsible for each use case.",
                    "answer_type": AssessmentQuestion.AnswerType.TEXT,
                    "weight": Decimal("0.00"),
                    "is_required": False,
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "purpose",
            "name": "Finalidade de uso",
            "description": "Purpose, tasks, and business context for AI-assisted routines.",
            "display_order": 3,
            "questions": [
                {
                    "code": "purpose-001",
                    "text": "Is the purpose of each AI use case formally documented?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
                },
                {
                    "code": "purpose-002",
                    "text": "Describe the routine, activities, users, and how AI outputs are used.",
                    "answer_type": AssessmentQuestion.AnswerType.TEXT,
                    "weight": Decimal("0.00"),
                    "is_required": True,
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "data-sharing",
            "name": "Informacoes compartilhadas",
            "description": "Data classification and information shared with AI tools.",
            "display_order": 4,
            "questions": [
                {
                    "code": "data-sharing-001",
                    "text": "Are data shared with AI tools classified by sensitivity before use?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
                {
                    "code": "data-sharing-002",
                    "text": "Describe the information shared with AI, including personal, sensitive, confidential, or strategic data.",
                    "answer_type": AssessmentQuestion.AnswerType.TEXT,
                    "weight": Decimal("0.00"),
                    "is_required": True,
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "ai-decisions",
            "name": "Decisoes influenciadas pela IA",
            "description": "Human impact and decision-making influenced by AI outputs.",
            "display_order": 5,
            "questions": [
                {
                    "code": "ai-decisions-001",
                    "text": "Are decisions influenced by AI identified, documented, and reviewed before affecting people or customers?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
            ],
        },
        {
            "code": "human-review",
            "name": "Revisao humana",
            "description": "Human validation and accountability for AI-generated outputs.",
            "display_order": 6,
            "questions": [
                {
                    "code": "human-review-001",
                    "text": "Is human review mandatory before AI outputs are used in relevant business processes?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
            ],
        },
        {
            "code": "governance",
            "name": "Governanca",
            "description": "Policies, training, ownership, and governance procedures for AI.",
            "display_order": 7,
            "questions": [
                {
                    "code": "governance-001",
                    "text": "Does the organization have a formal corporate AI usage policy?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
                {
                    "code": "governance-002",
                    "text": "Are employees trained on acceptable, secure, and responsible AI usage?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 2,
                },
            ],
        },
        {
            "code": "security",
            "name": "Seguranca",
            "description": "Security controls for AI access, data exposure, and incident handling.",
            "display_order": 8,
            "questions": [
                {
                    "code": "security-001",
                    "text": "Are security controls defined for access, data sharing, and incidents involving AI tools?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("3.00"),
                    "display_order": 1,
                },
            ],
        },
        {
            "code": "dependency",
            "name": "Dependencia operacional",
            "description": "Operational resilience and continuity when AI tools are unavailable.",
            "display_order": 9,
            "questions": [
                {
                    "code": "dependency-001",
                    "text": "Can critical business processes continue if the AI tools become unavailable?",
                    "answer_type": AssessmentQuestion.AnswerType.BOOLEAN,
                    "weight": Decimal("2.00"),
                    "display_order": 1,
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
                        "is_required": question_data.get("is_required", True),
                    },
                )
                question_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {framework.code} v{framework.version}: "
                f"{dimension_count} dimensions, {question_count} questions."
            )
        )
