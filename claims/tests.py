from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from .forms import ItemFormSet
from .models import Claim, ClaimItem


class ClaimTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('tester', password='test-only-password')
        self.claim = Claim.objects.create(department='88', branch='001', reporter='Tester', warehouse='CDC', created_by=self.user, updated_by=self.user)
        ClaimItem.objects.create(claim=self.claim, item_code='SKU-1', item_name='=SUM(1,2)', load=Decimal('10.125'), st_claim=Decimal('2.010'))

    def test_login_required(self):
        self.assertEqual(self.client.get('/claims/').status_code, 302)

    def test_permission_required(self):
        user = User.objects.create_user('viewer', password='test-only-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/claims/').status_code, 403)

    def test_diff_uses_decimal(self):
        self.assertEqual(self.claim.items.get().diff, Decimal('8.115'))

    def test_pages_render(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get('/'), '/claims/')
        for path in ['/claims/', '/claims/new/', f'/claims/{self.claim.pk}/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_csv_escapes_formula(self):
        self.client.force_login(self.user)
        response = self.client.get('/claims/export/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=SUM(1,2)", response.content.decode('utf-8-sig'))

    def test_item_required(self):
        formset = ItemFormSet({'items-TOTAL_FORMS': '0', 'items-INITIAL_FORMS': '0'}, instance=self.claim, prefix='items')
        self.assertFalse(formset.is_valid())

    def test_invalid_post_does_not_create_claim(self):
        self.client.force_login(self.user)
        response = self.client.post('/claims/new/', {'department': '88'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Claim.objects.count(), 1)

    def test_print_and_export_require_permission(self):
        user = User.objects.create_user('no-print-access')
        self.client.force_login(user)
        for path in ['/claims/print/', f'/claims/{self.claim.pk}/print/', f'/claims/{self.claim.pk}/export/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_print_document_shows_saved_data(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/claims/print/'), self.claim.number)
        response = self.client.get(f'/claims/{self.claim.pk}/print/')
        self.assertContains(response, self.claim.number)
        self.assertContains(response, 'SKU-1')
        self.assertContains(response, 'id="print"')

    def test_selected_csv_excludes_other_claims(self):
        other = Claim.objects.create(department='88', branch='002', reporter='Other', warehouse='CDC', created_by=self.user, updated_by=self.user)
        ClaimItem.objects.create(claim=other, item_code='OTHER-SKU', item_name='Other', load=1, st_claim=0)
        self.client.force_login(self.user)
        response = self.client.get(f'/claims/{self.claim.pk}/export/')
        self.assertContains(response, 'SKU-1')
        self.assertNotContains(response, 'OTHER-SKU')
        self.assertContains(response, "'=SUM(1,2)")

    def test_missing_print_document_returns_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/claims/999999/print/').status_code, 404)
        self.assertEqual(self.client.get('/claims/999999/export/').status_code, 404)
