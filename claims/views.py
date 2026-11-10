import csv
import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ClaimForm, ItemFormSet
from .models import Claim
from .csv_export import write_claims


def matches_version(value, claim):
    try:
        return bool(value) and parse_datetime(value) == claim.updated_at
    except (ValueError, TypeError):
        return False


def filtered(request):
    qs = Claim.objects.select_related('created_by')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(branch__icontains=q) | Q(branch_name__icontains=q) | Q(reporter__icontains=q))
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    return qs


@login_required
@permission_required('claims.view_claim', raise_exception=True)
def claim_list(request):
    return render(request, 'claims/list.html', {'page': Paginator(filtered(request), 20).get_page(request.GET.get('page')), 'statuses': Claim.STATUS})


@login_required
@permission_required('claims.change_claim', raise_exception=True)
@require_POST
def claim_status(request, pk):
    status = request.POST.get('status', '')
    previous = request.POST.get('previous_status', '')
    allowed = dict(Claim.STATUS)
    if status not in allowed or previous not in allowed:
        return JsonResponse({'error': 'สถานะไม่ถูกต้อง'}, status=400)
    with transaction.atomic():
        claim = get_object_or_404(Claim.objects.select_for_update(), pk=pk)
        if claim.status != previous or not matches_version(request.POST.get('version'), claim):
            return JsonResponse({'error': 'สถานะถูกเปลี่ยนโดยผู้ใช้อื่นแล้ว กรุณาโหลดหน้าใหม่'}, status=409)
        if claim.status != status:
            claim.status = status
            claim.updated_by = request.user
            claim.save(update_fields=['status', 'updated_by', 'updated_at'])
    return JsonResponse({'status': claim.status, 'label': claim.get_status_display(), 'version': claim.updated_at.isoformat()})


@login_required
@transaction.atomic
def claim_edit(request, pk=None):
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('claims.change_claim' if pk else 'claims.add_claim'):
        raise PermissionDenied
    if not pk and request.method == 'POST':
        number = request.POST.get('document_number', '').strip()
        existing = Claim.objects.filter(number=number).first() if number else None
        if existing:
            if not request.user.has_perm('claims.change_claim'):
                raise PermissionDenied
            messages.info(request, 'พบเลขที่เอกสารเดิม โหลดข้อมูลแล้ว กรุณาตรวจสอบและกดบันทึกเพื่ออัปเดตเอกสารเดิม')
            return redirect('claim_edit', pk=existing.pk)
    queryset = Claim.objects.select_for_update() if request.method == 'POST' else Claim.objects.all()
    instance = get_object_or_404(queryset, pk=pk) if pk else Claim()
    version = request.POST.get('version', '') if request.method == 'POST' else (instance.updated_at.isoformat() if pk else '')
    conflict = bool(pk and request.method == 'POST' and not matches_version(version, instance))
    form = ClaimForm(request.POST or None, instance=instance)
    items = ItemFormSet(request.POST or None, instance=instance, prefix='items')
    if request.method == 'POST':
        form_valid, items_valid = form.is_valid(), items.is_valid()
        if conflict:
            form.add_error(None, 'เอกสารนี้มีการแก้ไขหลังจากคุณเปิดหน้า ระบบไม่ได้บันทึกทับ ข้อมูลที่คุณกรอกยังอยู่ด้านล่าง กรุณาเปิดข้อมูลล่าสุดเพื่อเปรียบเทียบแล้วแก้ไขจากฉบับล่าสุด')
        if form_valid and items_valid and not conflict:
            try:
                with transaction.atomic():
                    claim = form.save(commit=False)
                    if not pk:
                        claim.created_by = request.user
                        if form.cleaned_data['document_number']:
                            claim.number = form.cleaned_data['document_number']
                    claim.updated_by = request.user
                    claim.save()
                    items.instance = claim
                    items.save()
            except IntegrityError:
                if not pk and Claim.objects.filter(number=form.cleaned_data['document_number']).exists():
                    form.add_error('document_number', 'เลขที่นี้เพิ่งถูกบันทึกโดยผู้ใช้อื่น กรุณาโหลดเอกสารเดิม')
                else:
                    raise
            else:
                messages.success(request, f'บันทึก {claim.number} เรียบร้อยแล้ว')
                return redirect('claim_edit', pk=claim.pk)
    fields = list(form)
    return render(request, 'claims/form.html', {'form': form, 'items': items, 'claim': instance, 'version': version, 'conflict': conflict, 'meta_fields': fields[:3], 'claim_fields': fields[3:16], 'transport_fields': fields[16:]}, status=409 if conflict else 200)


@never_cache
@login_required
@require_GET
def find_document(request):
    from django.core.exceptions import PermissionDenied
    if not (request.user.has_perm('claims.add_claim') or request.user.has_perm('claims.change_claim')):
        raise PermissionDenied
    number = request.GET.get('number', '').strip()
    if not number or len(number) > 40:
        return JsonResponse({'error': 'Invalid document number'}, status=400)
    claim = Claim.objects.filter(number=number).first()
    if claim is None:
        return JsonResponse({'found': False})
    if not request.user.has_perm('claims.change_claim'):
        raise PermissionDenied
    return JsonResponse({'found': True, 'url': reverse('claim_edit', args=[claim.pk])})


@login_required
@permission_required('claims.view_claim', raise_exception=True)
def export_csv(request, pk=None):
    claims = filtered(request)
    if pk is not None:
        selected = get_object_or_404(Claim, pk=pk)
        claims = Claim.objects.filter(pk=selected.pk)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"{re.sub(r'[^A-Za-z0-9_.-]', '_', selected.number)}.csv" if pk is not None else 'cdc-claims.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    write_claims(writer, claims.select_related('created_by', 'updated_by').prefetch_related('items').iterator(chunk_size=500))
    return response


@login_required
@permission_required('claims.view_claim', raise_exception=True)
def print_center(request):
    return render(request, 'claims/print_center.html', {
        'page': Paginator(filtered(request), 20).get_page(request.GET.get('page')),
        'statuses': Claim.STATUS,
    })


@login_required
@permission_required('claims.view_claim', raise_exception=True)
def print_document(request, pk):
    claim = get_object_or_404(Claim.objects.select_related('created_by', 'updated_by').prefetch_related('items'), pk=pk)
    details = []
    for name in ClaimForm().fields:
        if name == 'document_number':
            continue
        field = Claim._meta.get_field(name)
        value = getattr(claim, name)
        if field.choices:
            value = getattr(claim, f'get_{name}_display')()
        details.append((field.verbose_name, value))
    return render(request, 'claims/print_document.html', {'claim': claim, 'details': details})
