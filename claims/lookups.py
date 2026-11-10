from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import Claim, ClaimItem


# Suggest complete saved combinations rather than guessing a related value.
LOOKUP_GROUPS = {
    'department': (Claim, ('department', 'department_name')),
    'branch': (Claim, ('branch', 'branch_name')),
    'reporter': (Claim, ('reporter', 'reporter_position')),
    'approver': (Claim, ('approver', 'approver_position')),
    'vehicle': (Claim, ('vehicle_code', 'plate', 'vehicle_type', 'carrier')),
    'product': (ClaimItem, ('item_code', 'item_name', 'supplier')),
}


def configure_lookup_widgets(fields, model):
    for group, (lookup_model, names) in LOOKUP_GROUPS.items():
        if lookup_model is model:
            for name in names:
                fields[name].widget.attrs.update({
                    'data-lookup-group': group,
                    'data-lookup-field': name,
                    'autocomplete': 'off',
                    'role': 'combobox',
                    'aria-autocomplete': 'list',
                    'aria-expanded': 'false',
                })


@never_cache
@login_required
@require_GET
def suggestions(request):
    if not (request.user.has_perm('claims.add_claim') or request.user.has_perm('claims.change_claim')):
        raise PermissionDenied
    group = request.GET.get('group', '')
    if group not in LOOKUP_GROUPS:
        return JsonResponse({'error': 'Invalid lookup group'}, status=400)
    model, fields = LOOKUP_GROUPS[group]
    field = request.GET.get('field', '')
    if field not in fields:
        return JsonResponse({'error': 'Invalid lookup field'}, status=400)
    query = request.GET.get('q', '').strip()
    if not 2 <= len(query) <= 200:
        return JsonResponse({'results': []})
    # Records are already persisted atomically by the claim form. Existing data
    # and future successful saves immediately participate; drafts never do.
    updated = 'updated_at' if model is Claim else 'claim__updated_at'
    rows = (model.objects.filter(**{f'{field}__istartswith': query})
            .exclude(**{fields[0]: ''})
            .order_by().values(*fields).annotate(last_used=Max(updated))
            .order_by('-last_used', *fields)[:10])
    results = []
    for row in rows:
        values = {name: row[name] for name in fields}
        results.append({'label': ' · '.join(value for value in values.values() if value), 'values': values})
    return JsonResponse({'results': results})
