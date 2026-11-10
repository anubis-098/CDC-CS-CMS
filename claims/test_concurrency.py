from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth.models import User
from django.db import connection, connections
from django.test import Client, TransactionTestCase
from django.urls import reverse

from .models import Claim, ClaimItem


@skipUnless(connection.vendor == 'postgresql', 'Row locking requires PostgreSQL')
class ConcurrentClaimTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('concurrent-admin', password='Test-Password-951!')
        self.claim = Claim.objects.create(department='88', branch='001', reporter='Original', warehouse='CDC', created_by=self.user, updated_by=self.user)
        self.item = ClaimItem.objects.create(claim=self.claim, item_code='SKU', item_name='Product', load=10, st_claim=1)

    def payload(self, index, existing=True):
        data = {
            'document_number': self.claim.number if existing else f'CLIENT-{index}',
            'document_date': '2026-11-10', 'status': 'open', 'department': '88',
            'branch': '001', 'reporter': f'Client {index}', 'warehouse': 'CDC', 'seal_status': 'ปกติ',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '1' if existing else '0',
            'items-0-status': 'open', 'items-0-item_code': 'SKU', 'items-0-item_name': 'Product',
            'items-0-load': str(20 + index), 'items-0-st_claim': '1',
        }
        if existing:
            data.update(version=self.claim.updated_at.isoformat(), **{'items-0-id': str(self.item.pk)})
        return data

    def race(self, existing=True, same_number=False):
        barrier = Barrier(6)
        user_id = self.user.pk
        url = reverse('claim_edit', args=[self.claim.pk]) if existing else reverse('claim_new')

        def save(index):
            try:
                client = Client()
                client.force_login(User.objects.get(pk=user_id))
                data = self.payload(index, existing)
                if same_number:
                    data['document_number'] = 'SHARED-NEW-NUMBER'
                barrier.wait(timeout=15)
                response = client.post(url, data)
                return index, response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=6) as executor:
            return list(executor.map(save, range(6)))

    def test_six_editors_only_one_writes_same_version(self):
        results = self.race()
        winners = [index for index, status in results if status == 302]
        self.assertEqual(len(winners), 1)
        self.assertEqual(sum(status == 409 for _, status in results), 5)
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.claim.reporter, f'Client {winners[0]}')
        self.assertEqual(self.item.load, 20 + winners[0])
        self.assertEqual(ClaimItem.objects.count(), 1)

    def test_six_new_documents_all_save(self):
        self.assertTrue(all(status == 302 for _, status in self.race(existing=False)))
        self.assertEqual(Claim.objects.count(), 7)
        self.assertEqual(ClaimItem.objects.count(), 7)

    def test_same_new_number_never_duplicates_or_returns_server_error(self):
        results = self.race(existing=False, same_number=True)
        self.assertTrue(all(status in (200, 302) for _, status in results))
        claim = Claim.objects.get(number='SHARED-NEW-NUMBER')
        self.assertEqual(claim.items.count(), 1)

    def test_status_change_invalidates_open_form_and_old_status_requests(self):
        client = Client()
        client.force_login(self.user)
        url = reverse('claim_status', args=[self.claim.pk])
        token = self.claim.updated_at.isoformat()
        result = client.post(url, {'status': 'review', 'previous_status': 'open', 'version': token})
        self.assertEqual(result.status_code, 200)
        response = client.post(reverse('claim_edit', args=[self.claim.pk]), self.payload(1))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.context['form']['reporter'].value(), 'Client 1')
        self.assertEqual(response.context['version'], token)
        self.assertEqual(client.post(url, {'status': 'closed', 'previous_status': 'review', 'version': token}).status_code, 409)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'review')
        self.assertEqual(self.claim.reporter, 'Original')

    def test_missing_version_never_overwrites(self):
        client = Client()
        client.force_login(self.user)
        data = self.payload(0)
        data.pop('version')
        self.assertEqual(client.post(reverse('claim_edit', args=[self.claim.pk]), data).status_code, 409)
