from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from .forms import ClaimForm, ItemFormSet
from .models import Claim, ClaimItem


class SuggestionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('lookup-admin', password='Test-Password-951!')
        self.claim = Claim.objects.create(
            department='88', department_name='คลังสินค้า', branch='001', branch_name='บางนา',
            reporter='สมชาย', reporter_position='เจ้าหน้าที่', warehouse='CDC',
            created_by=self.user, updated_by=self.user,
        )
        self.client.force_login(self.user)

    def search(self, group='department', field='department', q='88'):
        return self.client.get(reverse('claim_suggestions'), {'group': group, 'field': field, 'q': q})

    def test_saved_pairs_are_searchable_in_both_directions(self):
        response = self.search()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['values'], {'department': '88', 'department_name': 'คลังสินค้า'})
        self.assertEqual(self.search(field='department_name', q='คล').json()['results'][0]['values']['department'], '88')
        self.assertEqual(self.search('branch', 'branch', '00').json()['results'][0]['values']['branch_name'], 'บางนา')
        self.assertEqual(self.search('reporter', 'reporter', 'สม').json()['results'][0]['values']['reporter_position'], 'เจ้าหน้าที่')
        self.assertIn('no-store', response['Cache-Control'])

    def test_minimum_length_and_allowlist(self):
        self.assertEqual(self.search(q='8').json()['results'], [])
        self.assertEqual(self.search(q='  ').json()['results'], [])
        self.assertEqual(self.search(group='created_by').status_code, 400)
        self.assertEqual(self.search(field='created_by__password').status_code, 400)

    def test_access_requires_login_and_claim_editing_permission(self):
        self.client.logout()
        self.assertEqual(self.search().status_code, 302)
        viewer = User.objects.create_user('lookup-viewer')
        viewer.user_permissions.add(Permission.objects.get(codename='view_claim'))
        self.client.force_login(viewer)
        self.assertEqual(self.search().status_code, 403)
        viewer.user_permissions.add(Permission.objects.get(codename='add_claim'))
        self.assertEqual(self.search().status_code, 200)

    def test_duplicate_combinations_collapsed(self):
        self.claim.pk = None
        self.claim.number = 'SECOND-DOCUMENT'
        self.claim.save()
        self.assertEqual(len(self.search().json()['results']), 1)

    def test_different_values_not_silently_merged(self):
        self.claim.pk = None
        self.claim.number = 'ANOTHER-DOCUMENT'
        self.claim.department_name = 'ฝ่ายอื่น'
        self.claim.save()
        self.assertEqual(len(self.search().json()['results']), 2)

    def test_limit_to_ten_suggestions(self):
        for index in range(12):
            Claim.objects.create(department=f'88{index}', department_name=f'Team {index}', branch='001', reporter='Reporter', warehouse='CDC', created_by=self.user, updated_by=self.user)
        self.assertEqual(len(self.search().json()['results']), 10)

    def test_dynamic_item_form_has_lookup_metadata(self):
        self.assertIn('data-lookup-group="department"', str(ClaimForm()['department']))
        self.assertIn('data-lookup-group="product"', str(ItemFormSet(prefix='items').empty_form['item_code']))
        ClaimItem.objects.create(claim=self.claim, item_code='SKU-01', item_name='Water', supplier='Supplier A', load=1, st_claim=0)
        result = self.search('product', 'item_code', 'SK').json()['results'][0]
        self.assertEqual(result['values']['item_name'], 'Water')

    def test_successful_form_save_becomes_available_and_invalid_save_does_not(self):
        data = {
            'document_date': '2026-11-10', 'status': 'open', 'department': 'ZZ',
            'department_name': 'New department', 'branch': '009', 'branch_name': 'New branch',
            'reporter': 'New reporter', 'warehouse': 'CDC', 'seal_status': 'ปกติ',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-0-status': 'open', 'items-0-item_code': 'NEW-SKU',
            'items-0-item_name': 'New product', 'items-0-load': '12', 'items-0-st_claim': '1',
        }
        self.assertEqual(self.client.post(reverse('claim_new'), data).status_code, 302)
        self.assertEqual(self.search(q='ZZ').json()['results'][0]['values']['department_name'], 'New department')
        data.update(department='XX', **{'items-0-load': '-1'})
        self.assertEqual(self.client.post(reverse('claim_new'), data).status_code, 200)
        self.assertEqual(self.search(q='XX').json()['results'], [])
