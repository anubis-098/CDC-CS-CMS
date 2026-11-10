from django import forms
from django.forms import inlineformset_factory
from .models import Claim, ClaimItem
from .lookups import configure_lookup_widgets


class ClaimForm(forms.ModelForm):
    document_number = forms.RegexField(regex=r'^[\w./-]+$', label='เลขที่เอกสาร', max_length=40, required=False,
                                     error_messages={'invalid': 'ใช้ตัวอักษร ตัวเลข จุด ขีดกลาง ขีดล่าง หรือ / โดยไม่เว้นวรรค'},
                                     widget=forms.TextInput(attrs={'placeholder': 'เช่น CLM-2026-0001', 'autocomplete': 'off', 'aria-describedby': 'document-lookup-status'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['document_number', *[name for name in self.fields if name != 'document_number']])
        if self.instance.pk:
            self.fields['document_number'].initial = self.instance.number
            self.fields['document_number'].disabled = True
        configure_lookup_widgets(self.fields, Claim)
        placeholders = {
            'department': 'เช่น 88',
            'department_name': 'เช่น ฝ่ายคลังสินค้า',
            'branch': 'เช่น 001',
            'branch_name': 'เช่น สาขาบางนา',
            'reporter': 'ชื่อ–นามสกุลผู้แจ้งเคลม',
            'reporter_position': 'เช่น เจ้าหน้าที่คลังสินค้า',
            'approver': 'ชื่อ–นามสกุลผู้อนุมัติ',
            'approver_position': 'เช่น หัวหน้าแผนก',
            'carrier': 'เช่น CJ Logistics',
            'vehicle_code': 'เช่น TRK-001',
            'plate': 'เช่น 1กข 1234',
            'vehicle_type': 'เช่น รถบรรทุก 6 ล้อ',
            'driver': 'ชื่อ–นามสกุลพนักงานขับรถ',
            'seal_code': 'เช่น SEAL-001',
            'extra_info': 'เช่น พบกล่องชำรุดขณะรับสินค้า',
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs['placeholder'] = placeholder
        self.fields['warehouse'].choices = [('', '-- เลือกคลัง --')] + [
            (value, label) for value, label in self.fields['warehouse'].choices if value
        ]

    def clean_document_number(self):
        number = self.cleaned_data['document_number'].strip()
        if not self.instance.pk and number and Claim.objects.filter(number=number).exists():
            raise forms.ValidationError('เลขที่นี้มีอยู่แล้ว กรุณาโหลดเอกสารเดิมก่อนแก้ไข')
        return number

    class Meta:
        model = Claim
        exclude = ['created_by', 'updated_by']
        widgets = {**{name: forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d') for name in ['document_date', 'received_date', 'paper_date']}, **{name: forms.TimeInput(attrs={'type': 'time'}) for name in ['received_time', 'paper_time']}, 'extra_info': forms.Textarea(attrs={'rows': 3})}


class ClaimItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_lookup_widgets(self.fields, ClaimItem)

    class Meta:
        model = ClaimItem
        fields = ['status', 'load_no', 'item_code', 'item_name', 'supplier', 'shipment_no', 'po_no', 'load', 'st_claim', 'remark']
        widgets = {
            name: forms.TextInput(attrs={'placeholder': placeholder})
            for name, placeholder in {
                'load_no': 'เช่น LD-001',
                'item_code': 'เช่น SKU-001',
                'item_name': 'เช่น น้ำดื่ม 600 มล.',
                'supplier': 'ชื่อ Supplier',
                'shipment_no': 'เช่น SHP-001',
                'po_no': 'เช่น PO-001',
                'remark': 'เช่น กล่องบุบ / สินค้าขาด',
            }.items()
        }
        widgets.update({name: forms.NumberInput(attrs={'placeholder': '0.000', 'min': '0', 'step': '0.001'}) for name in ['load', 'st_claim']})


ItemFormSet = inlineformset_factory(Claim, ClaimItem, form=ClaimItemForm, fields=ClaimItemForm.Meta.fields, extra=0, min_num=1, validate_min=True, max_num=200, validate_max=True, can_delete=True)
