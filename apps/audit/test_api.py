from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Membership, Organization

from .models import AuditEvent, DataChangeLog


class AuditApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
        self.client.force_authenticate(self.user)

    def test_list_audit_events_only_returns_user_organizations(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        visible_event = AuditEvent.objects.create(
            organization=self.organization,
            actor_user=self.user,
            event_type="organization.created",
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
        )
        AuditEvent.objects.create(
            organization=hidden_org,
            event_type="organization.created",
            entity_type="Organization",
            entity_uuid=hidden_org.uuid,
        )

        response = self.client.get("/api/audit-events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_uuids = {item["uuid"] for item in response.json()["results"]}
        self.assertIn(str(visible_event.uuid), event_uuids)

    def test_audit_events_are_read_only(self):
        response = self.client.post(
            "/api/audit-events/",
            {
                "event_type": "organization.created",
                "entity_type": "Organization",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_data_change_logs_only_returns_user_organizations(self):
        visible_event = AuditEvent.objects.create(
            organization=self.organization,
            actor_user=self.user,
            event_type="organization.updated",
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
        )
        visible_log = DataChangeLog.objects.create(
            audit_event=visible_event,
            entity_type="Organization",
            entity_uuid=self.organization.uuid,
            action=DataChangeLog.Action.UPDATE,
            before={"name": "Old"},
            after={"name": "Acme Corp"},
            changed_fields=["name"],
        )
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_event = AuditEvent.objects.create(
            organization=hidden_org,
            event_type="organization.updated",
            entity_type="Organization",
            entity_uuid=hidden_org.uuid,
        )
        DataChangeLog.objects.create(
            audit_event=hidden_event,
            entity_type="Organization",
            entity_uuid=hidden_org.uuid,
            action=DataChangeLog.Action.UPDATE,
        )

        response = self.client.get("/api/data-change-logs/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log_uuids = {item["uuid"] for item in response.json()["results"]}
        self.assertIn(str(visible_log.uuid), log_uuids)

