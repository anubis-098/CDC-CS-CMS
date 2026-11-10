from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import django.core.validators
import claims.models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Claim', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('number', models.CharField('เลขที่เอกสาร', max_length=40, unique=True, default=claims.models.claim_number, editable=False)),
            ('document_date', models.DateField('วันที่เอกสาร', default=timezone.localdate)),
            ('status', models.CharField('สถานะ', max_length=20, choices=[('open', 'เปิดรายการ'), ('review', 'รอตรวจสอบ'), ('processing', 'กำลังดำเนินการ'), ('closed', 'ปิดรายการ'), ('cancelled', 'ยกเลิก')], default='open')),
            ('department', models.CharField('รหัสแผนก', max_length=30)),
            ('department_name', models.CharField('ชื่อแผนก', max_length=150, blank=True)),
            ('branch', models.CharField('รหัสสาขา', max_length=30)),
            ('branch_name', models.CharField('ชื่อสาขา', max_length=150, blank=True)),
            ('reporter', models.CharField('ผู้แจ้งเคลม', max_length=150)),
            ('reporter_position', models.CharField('ตำแหน่งผู้แจ้ง', max_length=100, blank=True)),
            ('approver', models.CharField('ชื่อผู้อนุมัติ (ข้อมูลอ้างอิง)', max_length=150, blank=True)),
            ('approver_position', models.CharField('ตำแหน่งผู้อนุมัติ', max_length=100, blank=True)),
            ('received_date', models.DateField('วันที่รับสินค้า', null=True, blank=True)),
            ('received_time', models.TimeField('เวลารับสินค้า', null=True, blank=True)),
            ('paper_date', models.DateField('วันที่รับเอกสาร', null=True, blank=True)),
            ('paper_time', models.TimeField('เวลารับเอกสาร', null=True, blank=True)),
            ('warehouse', models.CharField('คลังสินค้า', max_length=20, choices=[(x, x) for x in ['CDC', 'MKO', 'FC', 'OTHER']])),
            ('carrier', models.CharField('บริษัทขนส่ง', max_length=150, blank=True)),
            ('vehicle_code', models.CharField('รหัสรถ', max_length=50, blank=True)),
            ('plate', models.CharField('ทะเบียนรถ', max_length=50, blank=True)),
            ('vehicle_type', models.CharField('ประเภทรถ', max_length=50, blank=True)),
            ('driver', models.CharField('พนักงานขับรถ', max_length=150, blank=True)),
            ('seal_status', models.CharField('สภาพซีล', max_length=30, choices=[(x, x) for x in ['ปกติ', 'ชำรุด', 'ไม่มีซีล', 'ไม่เกี่ยวข้อง']], default='ปกติ')),
            ('seal_code', models.CharField('รหัสซีล', max_length=50, blank=True)),
            ('extra_info', models.TextField('ข้อมูลเพิ่มเติม', blank=True)),
            ('created_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_claims')),
            ('updated_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='updated_claims')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ], options={'ordering': ['-created_at'], 'indexes': [models.Index(fields=['status', 'document_date'], name='claim_status_date_idx')]}),
        migrations.CreateModel(name='ClaimItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('claim', models.ForeignKey('claims.claim', on_delete=models.CASCADE, related_name='items')),
            ('status', models.CharField('สถานะ', max_length=20, choices=[('open', 'เปิดรายการ'), ('review', 'รอตรวจสอบ'), ('processing', 'กำลังดำเนินการ'), ('closed', 'ปิดรายการ'), ('cancelled', 'ยกเลิก')], default='open')),
            ('load_no', models.CharField('Load No.', max_length=60, blank=True)),
            ('item_code', models.CharField('รหัสสินค้า', max_length=60)),
            ('item_name', models.CharField('ชื่อสินค้า', max_length=200)),
            ('supplier', models.CharField('Supplier', max_length=150, blank=True)),
            ('shipment_no', models.CharField('Shipment No.', max_length=60, blank=True)),
            ('po_no', models.CharField('PO No.', max_length=60, blank=True)),
            ('load', models.DecimalField('Load', max_digits=14, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
            ('st_claim', models.DecimalField('ST claim', max_digits=14, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
            ('remark', models.CharField('หมายเหตุ', max_length=500, blank=True)),
        ], options={'constraints': [models.CheckConstraint(condition=models.Q(load__gte=0, st_claim__gte=0), name='nonnegative_quantities')]}),
    ]
