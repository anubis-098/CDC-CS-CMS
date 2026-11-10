from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from .models import Claim, ClaimItem


class DocumentNumberTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('number-admin', password='Test-Password-951!')
        self.client.force_login(self.admin)
        self.data = {
            'document_number': 'CLM-CUSTOM-001', 'document_date': '2026-11-10', 'status': 'open',
            'department': '88', 'department_name': 'Warehouse', 'branch': '001',
            'reporter': 'Reporter', 'warehouse': 'CDC', 'seal_status': 'ปกติ',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-0-status': 'open', 'items-0-item_code': 'SKU-1', 'items-0-item_name': 'Product',
            'items-0-load': '10', 'items-0-st_claim': '1',
        }

    def test_create_lookup_and_update_preserves_document_identity(self):
        self.assertEqual(self.client.post(reverse('claim_new'), self.data).status_code, 302)
        claim = Claim.objects.get(number=self.data['document_number'])
        old_created, old_updated = claim.created_at, claim.updated_at
        item = claim.items.get()
        lookup = self.client.get(reverse('find_document'), {'number': claim.number})
        self.assertEqual(lookup.json(), {'found': True, 'url': reverse('claim_edit', args=[claim.pk])})
        loaded = self.client.get(lookup.json()['url'])
        self.assertEqual(loaded.context['form']['department_name'].value(), 'Warehouse')
        self.assertEqual(loaded.context['items'].forms[0]['item_code'].value(), 'SKU-1')
        data = {**self.data, 'version': claim.updated_at.isoformat(), 'department_name': 'Updated', 'items-INITIAL_FORMS': '1', 'items-0-id': str(item.pk), 'items-0-load': '20'}
        self.assertEqual(self.client.post(lookup.json()['url'], data).status_code, 302)
        claim.refresh_from_db()
        self.assertEqual(Claim.objects.count(), 1)
        self.assertEqual(ClaimItem.objects.count(), 1)
        self.assertEqual(claim.created_at, old_created)
        self.assertGreater(claim.updated_at, old_updated)
        self.assertEqual(claim.department_name, 'Updated')
        self.assertEqual(claim.items.get().load, 20)
        printed = self.client.get(reverse('print_document', args=[claim.pk]))
        self.assertContains(printed, 'แก้ไขล่าสุด')
        self.assertEqual(printed.context['claim'].updated_at, claim.updated_at)

    def test_duplicate_new_post_loads_existing_without_replacing_items(self):
        self.client.post(reverse('claim_new'), self.data)
        claim = Claim.objects.get()
        response = self.client.post(reverse('claim_new'), {**self.data, 'reporter': 'Unexpected'})
        self.assertRedirects(response, reverse('claim_edit', args=[claim.pk]))
        claim.refresh_from_db()
        self.assertEqual(claim.reporter, 'Reporter')
        self.assertEqual(Claim.objects.count(), 1)
        self.assertEqual(ClaimItem.objects.count(), 1)

    def test_blank_number_is_generated(self):
        self.assertEqual(self.client.post(reverse('claim_new'), {**self.data, 'document_number': ''}).status_code, 302)
        self.assertTrue(Claim.objects.get().number.startswith('CLM-'))

    def test_add_only_user_cannot_load_or_overwrite_existing(self):
        self.client.post(reverse('claim_new'), self.data)
        user = User.objects.create_user('creator')
        user.user_permissions.add(Permission.objects.get(codename='add_claim'))
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('find_document'), {'number': self.data['document_number']}).status_code, 403)
        self.assertEqual(self.client.post(reverse('claim_new'), self.data).status_code, 403)
