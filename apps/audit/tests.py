from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.evidence.models import Evidence
from apps.organizations.models import Organization

from .models import AuditEvent, DataChangeLog
from .services import log_create_event


class AuditModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(
            name="Acme Corp",
            slug="acme-corp",
        )

    def test_create_audit_event(self):
        event = AuditEvent.objects.create(
            organization=self.organization,
            actor_user=self.user,
            event_type="organization.created",
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
            metadata={"source": "test"},
        )

        self.assertTrue(event.uuid)
        self.assertEqual(event.organization, self.organization)
        self.assertEqual(event.actor_user, self.user)
        self.assertEqual(event.metadata["source"], "test")

    def test_create_data_change_log(self):
        event = AuditEvent.objects.create(
            organization=self.organization,
            actor_user=self.user,
            event_type="organization.updated",
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
        )
        change = DataChangeLog.objects.create(
            audit_event=event,
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
            action=DataChangeLog.Action.UPDATE,
            before={"name": "Old name"},
            after={"name": "Acme Corp"},
            changed_fields=["name"],
        )

        self.assertEqual(change.audit_event, event)
        self.assertEqual(change.changed_fields, ["name"])

    def test_log_create_event_omits_sensitive_snapshot_fields(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
            description="Contains internal access process details.",
            external_url="https://example.com/private/access-policy",
            checksum="abc123",
        )

        event = log_create_event(
            actor_user=self.user,
            organization=self.organization,
            instance=evidence,
            event_type="evidence.uploaded",
        )

        change = event.change_logs.get()
        self.assertIn("title", change.after)
        self.assertIn("status", change.after)
        self.assertNotIn("description", change.after)
        self.assertNotIn("external_url", change.after)
        self.assertNotIn("checksum", change.after)
