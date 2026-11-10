from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse


class AccountManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', password='Original-Password-951!')
        self.member = User.objects.create_user('member', password='Original-Password-951!')
        self.payload = {'username': 'newmember', 'first_name': 'New', 'last_name': 'Member', 'email': 'new@example.com', 'role': 'officer', 'is_active': 'on', 'password1': 'Different-Strong-472!word', 'password2': 'Different-Strong-472!word'}

    def test_non_administrators_denied_get_and_post(self):
        self.member.is_staff = True
        self.member.save()
        self.member.user_permissions.set(Permission.objects.filter(content_type__app_label='auth'))
        self.client.force_login(self.member)
        for url in [reverse('account_list'), reverse('account_new'), reverse('account_edit', args=[self.admin.pk]), '/admin/auth/user/', f'/admin/auth/user/{self.admin.pk}/change/', '/admin/auth/group/']:
            for method in [self.client.get, self.client.post]:
                with self.subTest(url=url, method=method):
                    self.assertEqual(method(url, self.payload if method == self.client.post else {}).status_code, 403)

    def test_anonymous_redirects_to_login(self):
        self.assertEqual(self.client.get(reverse('account_list')).status_code, 302)

    def test_create_account_hashes_password_and_grants_officer(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('account_new'), self.payload)
        self.assertRedirects(response, reverse('account_list'))
        user = User.objects.get(username='newmember')
        self.assertTrue(user.check_password(self.payload['password1']))
        self.assertNotEqual(user.password, self.payload['password1'])
        self.assertTrue(user.has_perm('claims.change_claim'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_viewer_role_removes_previous_grants_and_keeps_password(self):
        self.client.force_login(self.admin)
        self.member.user_permissions.add(Permission.objects.get(codename='change_claim'))
        data = {**self.payload, 'username': self.member.username, 'role': 'viewer', 'password1': '', 'password2': ''}
        self.assertEqual(self.client.post(reverse('account_edit', args=[self.member.pk]), data).status_code, 302)
        user = User.objects.get(pk=self.member.pk)
        self.assertTrue(user.has_perm('claims.view_claim'))
        self.assertFalse(user.has_perm('claims.change_claim'))
        self.assertTrue(user.check_password('Original-Password-951!'))

    def test_cannot_disable_or_demote_self(self):
        self.client.force_login(self.admin)
        data = {**self.payload, 'username': self.admin.username, 'role': 'viewer', 'is_active': '', 'password1': '', 'password2': ''}
        response = self.client.post(reverse('account_edit', args=[self.admin.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('role', response.context['form'].errors)
        self.assertIn('is_active', response.context['form'].errors)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser and self.admin.is_active)

    def test_weak_password_and_duplicate_username_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('account_new'), {**self.payload, 'username': self.member.username, 'password1': '123', 'password2': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('password1', response.context['form'].errors)

    def test_self_password_change_preserves_session(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('account_edit', args=[self.admin.pk]), {**self.payload, 'username': self.admin.username, 'role': 'administrator'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse('account_list')).status_code, 200)

    def test_disabled_account_cannot_login(self):
        self.client.force_login(self.admin)
        data = {**self.payload, 'username': self.member.username, 'role': 'viewer', 'is_active': '', 'password1': '', 'password2': ''}
        self.client.post(reverse('account_edit', args=[self.member.pk]), data)
        self.client.logout()
        self.assertFalse(self.client.login(username=self.member.username, password='Original-Password-951!'))

    def test_administrator_pages_render(self):
        self.client.force_login(self.admin)
        for name, args in [('account_list', []), ('account_new', []), ('account_edit', [self.member.pk])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)
