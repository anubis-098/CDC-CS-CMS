# CDC Claim Management System

โครงเว็บ Python + PostgreSQL สำหรับงาน Claim Dry อ้างอิง `CJ_Claim_Management_System_example.html` โดยเก็บต้นฉบับไว้ครบ ใช้สีน้ำเงิน #006BB6 แดง #ED1C24 ส้ม #F7941D และ Google Fonts **Sarabun** ตัวอักษรแบรนด์เป็นข้อความ ยังไม่ใช่ไฟล์โลโก้ทางการ

## เริ่มใช้งาน

ติดตั้ง Docker Desktop พร้อม Docker Compose ก่อน จาก PowerShell ในโฟลเดอร์โปรเจกต์:

```powershell
Copy-Item .env.example .env
# แก้ DJANGO_SECRET_KEY และ POSTGRES_PASSWORD ใน .env
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

เปิด http://localhost:8085 แล้วใช้บัญชีที่สร้าง ระบบจะ migrate ฐานข้อมูลก่อนเริ่ม web และไม่สร้างบัญชีหรือข้อมูลตัวอย่างโดยอัตโนมัติ ฐานข้อมูลอยู่ใน volume `postgres_data` ไม่เปิดพอร์ต PostgreSQL สู่ภายนอก ค่าเริ่มต้นของเว็บผูกกับ localhost

## หน้าจอและขอบเขตที่ทำแล้ว

- หมวด 01 มีเลขที่เอกสารให้กรอกเอง (เว้นว่างเพื่อสร้างเลขอัตโนมัติ) เมื่อกรอกเลขเดิมแล้วออกจากช่องหรือกดโหลด จะเปิดฟอร์มแก้ไขพร้อมสินค้าทั้งหมด การบันทึกอัปเดตเอกสารเดิมและผู้แก้ไข/เวลาแก้ไขล่าสุด โดยคงผู้สร้างและวันสร้างเดิม หน้าพิมพ์แสดงเวลาแก้ไขถึงวินาที หาก POST เลขซ้ำจากหน้าใหม่โดยยังไม่ได้โหลด ระบบจะโหลดเอกสารเดิมให้ตรวจและกดบันทึกอีกครั้งเพื่อไม่ให้ข้อมูลเดิมถูกแทนที่ด้วยฟอร์มว่าง

- ฟอร์มเคลมมี autocomplete หลังพิมพ์ 2 ตัวอักษร ค้นจากต้นรหัส/ชื่อและเลือกเติมค่าคู่กัน: แผนก, สาขา, ผู้แจ้ง–ตำแหน่ง, ผู้อนุมัติ–ตำแหน่ง, รหัสรถ–ทะเบียน–ประเภทรถ–บริษัทขนส่ง และรหัสสินค้า–ชื่อ–Supplier รองรับคลิกหรือปุ่มลูกศร/Enter และ Escape เพื่อปิด
- รายการแนะนำมาจากข้อมูลใน Claim/ClaimItem ที่บันทึกสำเร็จแล้ว ใช้ข้อมูลเก่าได้โดยไม่ต้อง migrate เพิ่ม ไม่เก็บร่างที่ยังไม่บันทึก แสดงไม่เกิน 10 คู่ค่าที่ไม่ซ้ำ เรียงตามใช้งานล่าสุด หากแก้ไข/ลบข้อมูลเดิม คำแนะนำจะสะท้อนข้อมูลที่ยังมีในเอกสารปัจจุบัน ไม่ใช่ทะเบียน master แยกต่างหาก API นี้เข้าถึงได้เฉพาะผู้มีสิทธิ์สร้างหรือแก้ไขเคลม

- `/manage/accounts/` จัดการบัญชี เฉพาะ Administrator (`is_superuser`) รวมบัญชี superuser เดิม สร้าง/แก้ไขชื่อผู้ใช้ ชื่อ อีเมล ตั้งรหัสผ่าน กำหนด Role และปิด/เปิดบัญชี การปิดบัญชีจะทำให้เข้าระบบไม่ได้
- Role: Administrator จัดการทั้งหมด; Officer ดู/สร้าง/แก้ไขเคลม พิมพ์และส่งออก; Viewer ดู/พิมพ์/ส่งออก เมนูบัญชีและ endpoint ทั้ง GET/POST รวมหน้าจัดการ User/Group ใน Django Admin จำกัดเฉพาะ Administrator
- บันทึกบัญชีผ่านหน้าใหม่นี้จะใช้ Role แทน group และ direct permission เดิมทั้งหมด บัญชีเก่าที่ไม่มี Role แสดงว่า “ยังไม่ได้กำหนด Role” จนกว่า Administrator จะเลือกและบันทึก ไม่เปลี่ยนสิทธิ์บัญชีเก่าโดยอัตโนมัติ เว้นรหัสผ่านทั้งสองช่องเพื่อคงรหัสผ่านเดิม

- `/` เปลี่ยนเส้นทางไป `/claims/` ซึ่งเป็นหน้าแรกหลังเข้าสู่ระบบ
- `/claims/` ค้นหาด้วยเลขเอกสาร สาขา ผู้แจ้ง กรองสถานะ แบ่งหน้า และ Export CSV ตามตัวกรอง
- `/claims/new/` สร้างเคลม แยกข้อมูลเอกสาร การเคลม ขนส่ง และรายการสินค้า
- `/claims/<id>/` แก้ไข เพิ่ม/ลบรายการสินค้า พิมพ์ผ่าน browser และแสดงผู้แก้ไขล่าสุด
- `/accounts/login/` เข้าสู่ระบบ ใช้ session และ CSRF ของ Django
- `/admin/` จัดการผู้ใช้ กลุ่ม สิทธิ์ และเอกสาร สำหรับ staff

คงฟิลด์จากตัวอย่าง รวมสถานะสินค้า Supplier, Shipment, PO, วันที่/เวลารับสินค้าและเอกสาร จำนวนใช้ Decimal 3 ตำแหน่ง ค่า Diff คำนวณจาก Load − ST claim ฝั่งเซิร์ฟเวอร์ เลขเอกสารใช้วันที่กับ UUID suffix ไม่ใช่เลขรันตามปี บันทึกหัวเอกสารและรายการสินค้าใน transaction เดียว ต้องมีสินค้าอย่างน้อยหนึ่งรายการ

สิทธิ์เริ่มต้น: ผู้ใช้ต้องได้รับ `view_claim` เพื่อดูภาพรวม/รายการ/ส่งออก, `add_claim` เพื่อสร้าง, `change_claim` เพื่อแก้ไขหัวเอกสารและสินค้าภายในเอกสาร ผู้ใช้ที่ได้สิทธิ์จะเข้าถึงทุกสาขา การแยกสิทธิ์ตามสาขายังไม่ได้ทำ การเปิดหน้าแก้ไขต้องมี `change_claim` บัญชี superuser ใช้ตรวจสอบทุกหน้าได้

## ไลบรารีที่เลือก

| ส่วน | เครื่องมือ | เหตุผล |
| --- | --- | --- |
| Backend | Django 5.2 LTS | ORM, Forms, migrations, auth, permissions และ admin ในชุดเดียว |
| Database | PostgreSQL 17 + psycopg 3 | ข้อมูลสัมพันธ์ transaction และ Decimal |
| Frontend | Django Templates + CSS + JavaScript | โครงสร้างเรียบง่าย ไม่ต้องดูแล Node build ในการรันระบบ |
| HTTP server | Gunicorn | รัน Django ใน container |
| Static assets | WhiteNoise | เสิร์ฟ CSS/JS เมื่อ DEBUG=0 |
| Font | Sarabun / Google Fonts | อ่านภาษาไทยได้ชัดเจน มี fallback sans-serif เมื่อไม่มีอินเทอร์เน็ต |

ไลบรารีสำหรับระยะถัดไป: Django REST Framework เมื่อจำเป็นต้องเปิด API, openpyxl สำหรับ Excel .xlsx, Celery + Redis เมื่อต้องมีงานเบื้องหลัง ชุดนี้ยังไม่ติดตั้งส่วนที่ยังไม่มีการใช้งานจริง requirements จำกัด major/minor แต่ยังไม่ใช่ lockfile ควร lock เวอร์ชันหลังทดสอบในสภาพแวดล้อมที่จะ deploy

อ้างอิง: [Django 5.2](https://docs.djangoproject.com/en/5.2/releases/5.2/), [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)

## โครงสร้าง

```text
config/                  Django settings, URL routing, WSGI
claims/
  models.py              Claim และ ClaimItem
  forms.py               แบบฟอร์มและ inline formset
  views.py               Dashboard, search, create/edit, CSV
  admin.py               หน้าจัดการหลังบ้าน
  migrations/            โครงสร้างฐานข้อมูลรุ่นแรก
  tests.py               tests ของสิทธิ์ ข้อมูล และหน้าจอ
templates/               Layout, Dashboard, list, form, login
static/                  CJ-inspired CSS และ dynamic item rows
Dockerfile               Python application image
compose.yaml             db → migration job → web
.env.example             ตัวอย่าง environment configuration
docs/architecture.md     โครงสร้างระบบและแผนพัฒนาต่อ
```

## ตรวจสอบ

```powershell
docker compose config --quiet
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py test
```

ตรวจ syntax JavaScript ด้วย `node --check static/app.js` แล้ว แต่เครื่องที่สร้างโปรเจกต์ไม่พบ Python/Docker ใน PATH จึงยังไม่ได้รัน Django tests, migrations, Docker build หรือ visual browser QA ต้องรันคำสั่งด้านบนก่อนนำไปใช้งานจริง

## ขอบเขตระยะต่อไป

นี่เป็นโครงระบบเริ่มต้น ยังไม่มีขั้นอนุมัติบังคับตามบทบาท: ช่องผู้อนุมัติเป็นข้อมูลอ้างอิงและผู้มีสิทธิ์แก้ไขเลือกสถานะได้ ยังไม่มีประวัติแก้ไขทุกเวอร์ชัน ไฟล์แนบ หรืออีเมลแจ้งเตือน CSV ส่งออกครบทุกช่องข้อมูลเอกสารและสินค้า รวมผู้สร้าง/ผู้แก้ไขและวันเวลา โดยหนึ่งสินค้าต่อหนึ่งแถวและข้อมูลหัวเอกสารซ้ำทุกแถว มี 40 คอลัมน์ ใช้ UTF-8 BOM และเวลาประเทศไทย CSV นี้ไม่ใช่ไฟล์สำรองฐานข้อมูลสำหรับ restore

ก่อนเปิดใช้งานผ่านเครือข่ายจริง ให้เพิ่ม HTTPS reverse proxy, secure session/CSRF cookies, กำหนด host/domain, นโยบายสิทธิ์ตามสาขา และแผน backup/restore PostgreSQL ทดสอบการกู้คืนข้อมูลด้วย ไม่ใช้ `docker compose down -v` หากต้องการเก็บฐานข้อมูล


## ใช้งานหลาย client

ดู [คู่มือใช้งานหลาย client และป้องกันข้อมูลชน](docs/multi-client.md) ระบบตรวจ version และ lock เอกสารก่อนบันทึก เอกสารที่ถูกแก้ไปแล้วจะไม่ถูกบันทึกทับจากฟอร์มเก่า
