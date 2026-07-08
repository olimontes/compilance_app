from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import AssessmentDimension, AssessmentFramework, AssessmentQuestion


class SeedAssessmentFrameworksCommandTests(TestCase):
    def test_seed_assessment_frameworks_is_idempotent(self):
        output = StringIO()

        call_command("seed_assessment_frameworks", stdout=output)
        call_command("seed_assessment_frameworks", stdout=output)

        framework = AssessmentFramework.objects.get(code="AIGOV", version="1.0")
        self.assertEqual(framework.status, AssessmentFramework.Status.PUBLISHED)
        self.assertEqual(AssessmentDimension.objects.filter(framework=framework).count(), 9)
        self.assertEqual(AssessmentQuestion.objects.filter(framework=framework).count(), 14)
        self.assertIn("Seeded AIGOV v1.0", output.getvalue())
