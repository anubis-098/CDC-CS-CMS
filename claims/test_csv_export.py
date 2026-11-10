import csv
import io
from datetime import date, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .csv_export import CLAIM_COLUMNS, ITEM_COLUMNS
from .models import Claim, ClaimItem


class FullCsvExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('csv-admin', password='Test-Password-951!')
        self.client.force_login(self.user)
        self.claim = Claim.objects.create(
            number='CSV-001', department='88', department_name='คลังสินค้า', branch='001', branch_name='บางนา',
            reporter='ผู้แจ้ง', reporter_position='เจ้าหน้าที่', approver='ผู้อนุมัติ', approver_position='หัวหน้า',
            received_date=date(2026, 11, 10), received_time=time(9, 30), paper_date=date(2026, 11, 11), paper_time=time(10, 15),
            warehouse='CDC', carrier='CJ Logistics', vehicle_code='TRK-01', plate='1กข 1234', vehicle_type='6 ล้อ',
            driver='ผู้ขับรถ', seal_status='ชำรุด', seal_code='SEAL-01', extra_info='บรรทัดแรก, "ข้อความ"\nบรรทัดสอง',
            created_by=self.user, updated_by=self.user,
        )

    def export_rows(self):
        response = self.client.get(reverse('claim_export', args=[self.claim.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'\xef\xbb\xbf'))
        return list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))

    def test_all_business_fields_are_in_export_schema(self):
        claim_fields = {field.name for field in Claim._meta.fields} - {'id'}
        item_fields = {field.name for field in ClaimItem._meta.fields} - {'id', 'claim'}
        self.assertEqual({name for name, _ in CLAIM_COLUMNS}, claim_fields)
        self.assertEqual({name for name, _ in ITEM_COLUMNS}, item_fields | {'diff'})

    def test_all_items_and_complete_header_values_export(self):
        for index in range(2):
            ClaimItem.objects.create(claim=self.claim, status='review', load_no='LD-01', item_code=f'SKU-{index}', item_name='สินค้า', supplier='Supplier', shipment_no='SHP-01', po_no='PO-01', load=Decimal('1.125'), st_claim=Decimal('2.250'), remark='=SUM(1,2)')
        rows = self.export_rows()
        self.assertEqual(len(rows), 2)
        for index, row in enumerate(rows):
            self.assertEqual(len(row), 40)
            self.assertEqual(row['เลขที่เอกสาร'], 'CSV-001')
            self.assertEqual(row['ชื่อสาขา'], 'บางนา')
            self.assertEqual(row['ตำแหน่งผู้แจ้ง'], 'เจ้าหน้าที่')
            self.assertEqual(row['วันที่รับสินค้า'], '2026-11-10')
            self.assertEqual(row['เวลารับสินค้า'], '09:30:00')
            self.assertEqual(row['ทะเบียนรถ'], '1กข 1234')
            self.assertEqual(row['ข้อมูลเพิ่มเติม'], self.claim.extra_info)
            self.assertEqual(row['รหัสสินค้า'], f'SKU-{index}')
            self.assertEqual(row['สถานะรายการสินค้า'], 'รอตรวจสอบ')
            self.assertEqual(row['Diff'], '-1.125')
            self.assertEqual(row['หมายเหตุสินค้า'], "'=SUM(1,2)")
            self.assertIn('+07:00', row['วันที่แก้ไขล่าสุด (Asia/Bangkok)'])
            self.assertEqual(row['ผู้แก้ไขล่าสุด'], self.user.username)

    def test_header_is_exported_even_without_items(self):
        rows = self.export_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['เลขที่เอกสาร'], self.claim.number)
        self.assertEqual(rows[0]['รหัสสินค้า'], '')
