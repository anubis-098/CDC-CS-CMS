from datetime import datetime, date, time
from decimal import Decimal

from django.utils import timezone


CLAIM_COLUMNS = [
    ('number', 'เลขที่เอกสาร'), ('document_date', 'วันที่เอกสาร'), ('status', 'สถานะเอกสาร'),
    ('department', 'รหัสแผนก'), ('department_name', 'ชื่อแผนก'),
    ('branch', 'รหัสสาขา'), ('branch_name', 'ชื่อสาขา'),
    ('reporter', 'ผู้แจ้งเคลม'), ('reporter_position', 'ตำแหน่งผู้แจ้ง'),
    ('approver', 'ผู้อนุมัติ'), ('approver_position', 'ตำแหน่งผู้อนุมัติ'),
    ('received_date', 'วันที่รับสินค้า'), ('received_time', 'เวลารับสินค้า'),
    ('paper_date', 'วันที่รับเอกสาร'), ('paper_time', 'เวลารับเอกสาร'),
    ('warehouse', 'คลังสินค้า'), ('carrier', 'บริษัทขนส่ง'),
    ('vehicle_code', 'รหัสรถ'), ('plate', 'ทะเบียนรถ'), ('vehicle_type', 'ประเภทรถ'),
    ('driver', 'พนักงานขับรถ'), ('seal_status', 'สภาพซีล'), ('seal_code', 'รหัสซีล'),
    ('extra_info', 'ข้อมูลเพิ่มเติม'), ('created_by', 'ผู้สร้างเอกสาร'),
    ('created_at', 'วันที่สร้าง (Asia/Bangkok)'), ('updated_by', 'ผู้แก้ไขล่าสุด'),
    ('updated_at', 'วันที่แก้ไขล่าสุด (Asia/Bangkok)'),
]
ITEM_COLUMNS = [
    ('status', 'สถานะรายการสินค้า'), ('load_no', 'Load No.'), ('item_code', 'รหัสสินค้า'),
    ('item_name', 'ชื่อสินค้า'), ('supplier', 'Supplier'), ('shipment_no', 'Shipment No.'),
    ('po_no', 'PO No.'), ('load', 'Load'), ('st_claim', 'ST claim'), ('diff', 'Diff'),
    ('remark', 'หมายเหตุสินค้า'),
]


def cell(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        return timezone.localtime(value).isoformat(timespec='seconds')
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, '.3f')
    text = str(value)
    # Prevent text supplied by users from being evaluated as spreadsheet formulas.
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')) else text


def values(instance, columns):
    result = []
    for name, _ in columns:
        value = getattr(instance, name)
        display = getattr(instance, f'get_{name}_display', None)
        if display:
            value = display()
        if name in ('created_by', 'updated_by'):
            full_name = value.get_full_name()
            value = f'{value.username} ({full_name})' if full_name else value.username
        result.append(cell(value))
    return result


def write_claims(writer, claims):
    writer.writerow([label for _, label in CLAIM_COLUMNS] + ['ลำดับสินค้า'] + [label for _, label in ITEM_COLUMNS])
    for claim in claims:
        header = values(claim, CLAIM_COLUMNS)
        items = sorted(claim.items.all(), key=lambda item: item.pk)
        if not items:
            writer.writerow(header + [''] * (1 + len(ITEM_COLUMNS)))
        for index, item in enumerate(items, 1):
            writer.writerow(header + [index] + values(item, ITEM_COLUMNS))
