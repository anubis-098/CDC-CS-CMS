from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from claims import views
from claims import accounts
from claims.lookups import suggestions

urlpatterns_print = [
    path('claims/print/', views.print_center, name='print_center'),
    path('claims/<int:pk>/print/', views.print_document, name='print_document'),
    path('claims/<int:pk>/export/', views.export_csv, name='claim_export'),
]

urlpatterns = [path('admin/', admin.site.urls), path('accounts/', include('django.contrib.auth.urls')), path('', RedirectView.as_view(pattern_name='claim_list', permanent=False), name='home'), path('claims/', views.claim_list, name='claim_list'), path('claims/new/', views.claim_edit, name='claim_new'), path('claims/<int:pk>/', views.claim_edit, name='claim_edit'), path('claims/export/', views.export_csv, name='export_csv')]
urlpatterns += urlpatterns_print
urlpatterns += [
    path('claims/<int:pk>/status/', views.claim_status, name='claim_status'),
    path('claims/find-document/', views.find_document, name='find_document'),
    path('claims/suggestions/', suggestions, name='claim_suggestions'),
    path('manage/accounts/', accounts.account_list, name='account_list'),
    path('manage/accounts/new/', accounts.account_edit, name='account_new'),
    path('manage/accounts/<int:pk>/', accounts.account_edit, name='account_edit'),
]
