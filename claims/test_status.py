from django.contrib.auth.models import Permission, User
from django.test import Client, TestCase
from django.urls import reverse
from .models import Claim


class ClaimStatusTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner')
        self.editor = User.objects.create_user('editor')
        self.editor.user_permissions.add(Permission.objects.get(codename='change_claim'))
        self.claim = Claim.objects.create(department='88', branch='001', reporter='Reporter', warehouse='CDC', created_by=self.owner, updated_by=self.owner)
        self.url = reverse('claim_status', args=[self.claim.pk])
        self.client.force_login(self.editor)

    def test_updates_status_and_audit_without_changing_other_fields(self):
        created, updated = self.claim.created_at, self.claim.updated_at
        response = self.client.post(self.url, {'status': 'review', 'previous_status': 'open', 'version': self.claim.updated_at.isoformat(), 'reporter': 'Unexpected'})
        self.assertEqual(response.status_code, 200)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'review')
        self.assertEqual(self.claim.updated_by, self.editor)
        self.assertGreater(self.claim.updated_at, updated)
        self.assertEqual(self.claim.created_at, created)
        self.assertEqual(self.claim.reporter, 'Reporter')

    def test_invalid_and_stale_status_rejected(self):
        self.assertEqual(self.client.post(self.url, {'status': 'invalid', 'previous_status': 'open'}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {'status': 'closed', 'previous_status': 'review'}).status_code, 409)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'open')

    def test_get_and_unauthorized_requests_rejected(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.url, {'status': 'closed', 'previous_status': 'open'}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'status': 'closed', 'previous_status': 'open'}).status_code, 302)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        self.assertEqual(client.post(self.url, {'status': 'closed', 'previous_status': 'open'}).status_code, 403)

    def test_view_only_account_sees_badge_not_control(self):
        self.owner.user_permissions.add(Permission.objects.get(codename='view_claim'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('claim_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="claim-status-form"')
