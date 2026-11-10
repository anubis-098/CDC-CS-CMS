from functools import wraps

from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render


ROLES = [('administrator', 'Administrator'), ('officer', 'Officer'), ('viewer', 'Viewer')]
ROLE_GROUPS = {'officer': 'CDC Officer', 'viewer': 'CDC Viewer'}


def administrator_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def role_for(user):
    if user.is_superuser:
        return 'administrator'
    names = {group.name for group in user.groups.all()}
    if ROLE_GROUPS['officer'] in names:
        return 'officer'
    if ROLE_GROUPS['viewer'] in names:
        return 'viewer'
    return ''


class AccountForm(forms.ModelForm):
    role = forms.ChoiceField(label='Role', choices=ROLES)
    password1 = forms.CharField(label='รหัสผ่านใหม่', required=False, strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='ยืนยันรหัสผ่าน', required=False, strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {'username': 'ชื่อผู้ใช้', 'first_name': 'ชื่อ', 'last_name': 'นามสกุล', 'email': 'อีเมล', 'is_active': 'เปิดใช้งานบัญชี'}

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['role'].initial = role_for(self.instance) if self.instance.pk else 'viewer'
        if not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            self.add_error('password2', 'รหัสผ่านทั้งสองช่องไม่ตรงกัน')
        if self.instance.pk == self.actor.pk:
            if data.get('role') != 'administrator':
                self.add_error('role', 'ไม่สามารถลดสิทธิ์ Administrator ของบัญชีที่กำลังใช้งานได้')
            if not data.get('is_active'):
                self.add_error('is_active', 'ไม่สามารถปิดบัญชีที่กำลังใช้งานได้')
        return data

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password1')
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password1', error)

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        role = self.cleaned_data['role']
        user.is_superuser = role == 'administrator'
        user.is_staff = user.is_superuser
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        user.save()
        # Roles are authoritative: remove stale per-user and group grants.
        user.user_permissions.clear()
        if role == 'administrator':
            user.groups.clear()
        else:
            group, _ = Group.objects.get_or_create(name=ROLE_GROUPS[role])
            codes = ['view_claim', 'view_claimitem']
            if role == 'officer':
                codes += ['add_claim', 'change_claim', 'add_claimitem', 'change_claimitem', 'delete_claimitem']
            group.permissions.set(Permission.objects.filter(content_type__app_label='claims', codename__in=codes))
            user.groups.set([group])
        return user


@administrator_required
def account_list(request):
    users = User.objects.prefetch_related('groups').order_by('username')
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    page = Paginator(users, 20).get_page(request.GET.get('page'))
    for user in page:
        user.role_label = dict(ROLES).get(role_for(user), 'ยังไม่ได้กำหนด Role')
    return render(request, 'accounts/list.html', {'page': page})


@administrator_required
def account_edit(request, pk=None):
    account = get_object_or_404(User, pk=pk) if pk else User()
    form = AccountForm(request.POST if request.method == 'POST' else None, instance=account, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        account = form.save()
        if account.pk == request.user.pk:
            update_session_auth_hash(request, account)
        messages.success(request, f'บันทึกบัญชี {account.username} เรียบร้อยแล้ว')
        return redirect('account_list')
    return render(request, 'accounts/form.html', {'form': form, 'account': account})
