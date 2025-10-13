# 🎓 دانشکده هوش و مکاترونیک - سامانه مدیریت کلاس‌ها

سیستم جامع مدیریت برنامه کلاسی دانشکده با استفاده از Django، Django REST Framework و MySQL

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگیها)
- [تکنولوژی‌های استفاده شده](#تکنولوژیهای-استفاده-شده)
- [پیش‌نیازها](#پیشنیازها)
- [نصب و راه‌اندازی](#نصب-و-راهاندازی)
- [پیکربندی پایگاه داده](#پیکربندی-پایگاه-داده)
- [اجرای پروژه](#اجرای-پروژه)
- [ساختار پروژه](#ساختار-پروژه)
- [API Documentation](#api-documentation)
- [استفاده از پنل ادمین](#استفاده-از-پنل-ادمین)
- [مشارکت در توسعه](#مشارکت-در-توسعه)

## ✨ ویژگی‌ها

### بخش Frontend
- 🎨 رابط کاربری زیبا و مدرن با رنگ‌بندی آبی، سفید و مشکی
- 📱 طراحی کاملاً ریسپانسیو (موبایل، تبلت، دسکتاپ)
- 🍔 منوی همبرگری برای نمایش موبایل
- 🏠 صفحه خانه با بخش Hero تمام صفحه
- 🔍 **جستجوی سریع استاد** در صفحه اصلی با autocomplete
- 📅 انتخاب روز و زمان کلاس با UI تعاملی
- 🏢 نمایش بصری طبقات با نمایش راهرو و اتاق‌های چپ/راست
- ⚡ انیمیشن‌های روان و جذاب
- 🎯 UX بهینه شده برای دسترسی سریع به اطلاعات

### بخش Backend
- 🔐 پنل ادمین قدرتمند با رابط فارسی
- 📊 مدیریت اساتید، دروس، اتاق‌ها و برنامه کلاسی
- ✅ اعتبارسنجی داده‌ها و جلوگیری از تداخل کلاس‌ها
- 🔍 فیلتر و جستجوی پیشرفته
- 📡 RESTful API برای دسترسی برنامه‌نویسی
- 🗄️ MySQL برای مدیریت داده‌های مقیاس‌پذیر
- 📝 کامنت‌گذاری کامل کد
- 🛡️ مدیریت خطاهای حرفه‌ای

### قابلیت‌های خاص
- ✅ جلوگیری از رزرو همزمان یک اتاق
- ✅ جلوگیری از تداخل کلاس‌های یک استاد
- 🔍 **جستجوی فوری استاد** با انتخاب روز و نمایش تمام کلاس‌ها
- 💡 **Autocomplete هوشمند** برای نام اساتید
- 📊 نمایش ظرفیت هر کلاس
- 🏗️ معماری مقیاس‌پذیر برای توسعه آینده
- 🎨 UI/UX حرفه‌ای و خلاقانه

## 🛠 تکنولوژی‌های استفاده شده

### Backend
- **Django 4.2.7** - فریمورک اصلی
- **Django REST Framework 3.14.0** - API
- **MySQL** - پایگاه داده
- **mysqlclient 2.2.0** - درایور MySQL
- **django-filter 23.5** - فیلترینگ API
- **django-cors-headers 4.3.0** - مدیریت CORS

### Frontend
- **HTML5** - ساختار صفحات
- **CSS3** - استایل‌دهی و انیمیشن
- **JavaScript (Vanilla)** - تعاملات
- **Vazirmatn Font** - فونت فارسی

## 📦 پیش‌نیازها

قبل از شروع، موارد زیر را نصب کنید:

- **Python 3.8+** ([دانلود](https://www.python.org/downloads/))
- **MySQL 8.0+** ([دانلود](https://dev.mysql.com/downloads/mysql/))
- **pip** (معمولاً با Python نصب می‌شود)
- **virtualenv** (اختیاری اما توصیه می‌شود)

## 🚀 نصب و راه‌اندازی

### 1. کلون کردن پروژه

اگر از Git استفاده می‌کنید:

```bash
git clone <repository-url>
cd "UNI HUSH"
```

### 2. ایجاد محیط مجازی

برای ویندوز:
```bash
python -m venv venv
venv\Scripts\activate
```

برای لینوکس/مک:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

اگر با خطای نصب `mysqlclient` مواجه شدید:

**ویندوز:**
1. دانلود wheel file از [اینجا](https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient)
2. نصب با: `pip install mysqlclient‑2.x.x‑cpxx‑cpxxm‑win_amd64.whl`

**لینوکس:**
```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

## 🗄️ پیکربندی پایگاه داده

### 1. ایجاد دیتابیس MySQL

وارد MySQL شوید:
```bash
mysql -u root -p
```

دیتابیس را ایجاد کنید:
```sql
CREATE DATABASE university_hub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

(اختیاری) ایجاد کاربر اختصاصی:
```sql
CREATE USER 'uni_admin'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON university_hub.* TO 'uni_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. پیکربندی تنظیمات Django

فایل `university_hub/settings.py` را باز کنید و تنظیمات دیتابیس را بررسی کنید:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'university_hub',
        'USER': 'root',  # یا 'uni_admin'
        'PASSWORD': '',  # رمز عبور خود را وارد کنید
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

### 3. اعمال مهاجرت‌ها

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. ایجاد سوپریوزر

```bash
python manage.py createsuperuser
```

نام کاربری، ایمیل و رمز عبور را وارد کنید.

## ▶️ اجرای پروژه

### 1. جمع‌آوری فایل‌های Static

```bash
python manage.py collectstatic
```

### 2. اجرای سرور Development

```bash
python manage.py runserver
```

سایت در آدرس زیر در دسترس است:
- **وبسایت اصلی:** http://127.0.0.1:8000/
- **پنل ادمین:** http://127.0.0.1:8000/admin/
- **API:** http://127.0.0.1:8000/api/

## 📁 ساختار پروژه

```
UNI HUSH/
├── university_hub/          # تنظیمات اصلی پروژه
│   ├── settings.py         # تنظیمات Django
│   ├── urls.py             # URL routing اصلی
│   ├── wsgi.py             # WSGI config
│   └── asgi.py             # ASGI config
├── classes/                # اپلیکیشن اصلی
│   ├── models.py           # مدل‌های دیتابیس
│   ├── views.py            # ویوهای وبسایت
│   ├── admin.py            # پیکربندی پنل ادمین
│   ├── urls.py             # URL routing
│   ├── api_views.py        # ویوهای API
│   ├── api_urls.py         # URL routing API
│   └── serializers.py      # سریالایزرهای DRF
├── templates/              # قالب‌های HTML
│   ├── base.html           # قالب پایه
│   └── classes/            # قالب‌های اپ
│       ├── home.html
│       ├── class_affairs.html
│       ├── time_selection.html
│       ├── floor_view.html
│       └── error.html
├── static/                 # فایل‌های استاتیک
│   ├── css/
│   │   └── style.css       # استایل اصلی
│   ├── js/
│   │   └── script.js       # جاوااسکریپت اصلی
│   └── images/
│       └── hero-bg.jpg     # تصویر پس‌زمینه
├── media/                  # فایل‌های آپلود شده
├── venv/                   # محیط مجازی
├── manage.py               # ابزار مدیریت Django
├── requirements.txt        # وابستگی‌ها
└── README.md              # این فایل
```

## 🔌 API Documentation

### Endpoints اصلی

#### Teachers (اساتید)
```
GET /api/teachers/          - لیست اساتید
GET /api/teachers/{id}/     - جزئیات استاد
```

#### Courses (دروس)
```
GET /api/courses/           - لیست دروس
GET /api/courses/{id}/      - جزئیات درس
```

#### Floors (طبقات)
```
GET /api/floors/            - لیست طبقات
GET /api/floors/{id}/       - جزئیات طبقه
```

#### Rooms (اتاق‌ها)
```
GET /api/rooms/             - لیست اتاق‌ها
GET /api/rooms/{id}/        - جزئیات اتاق
GET /api/rooms/?floor=1     - فیلتر بر اساس طبقه
```

#### Class Schedules (برنامه کلاسی)
```
GET /api/schedules/                                    - لیست برنامه‌ها
GET /api/schedules/{id}/                               - جزئیات برنامه
GET /api/schedules/?day_of_week=saturday               - فیلتر بر اساس روز
GET /api/schedules/?time_slot=08:00                    - فیلتر بر اساس زمان
GET /api/schedules/by_day_and_time/?day=saturday&time=08:00  - فیلتر ترکیبی
GET /api/schedules/by_teacher_and_day/?teacher=احمدی&day=saturday  - جستجوی استاد
```

### نمونه پاسخ API

```json
{
    "id": 1,
    "teacher_name": "دکتر احمدی",
    "course_code": "AI-401",
    "course_name": "هوش مصنوعی پیشرفته",
    "room_number": "301",
    "room_capacity": 40,
    "floor_name": "طبقه سوم",
    "day_of_week": "saturday",
    "day_display": "شنبه",
    "time_slot": "08:00",
    "time_display": "کلاس‌های 8 صبح",
    "is_active": true
}
```

## 👨‍💼 استفاده از پنل ادمین

### ورود به پنل
1. به آدرس http://127.0.0.1:8000/admin/ بروید
2. با اطلاعات سوپریوزر وارد شوید

### مدیریت داده‌ها

#### 1. اضافه کردن طبقات
- به بخش "طبقات" بروید
- شماره و نام طبقه را وارد کنید (مثلاً: 1 - طبقه اول)

#### 2. اضافه کردن اتاق‌ها
- به بخش "اتاق‌ها" بروید
- طبقه، شماره اتاق، نوع، ظرفیت و موقعیت را وارد کنید

#### 3. اضافه کردن اساتید
- به بخش "اساتید" بروید
- نام کامل و اطلاعات تماس را وارد کنید

#### 4. اضافه کردن دروس
- به بخش "دروس" بروید
- کد درس، نام و تعداد واحد را وارد کنید

#### 5. ایجاد برنامه کلاسی
- به بخش "برنامه‌های کلاسی" بروید
- استاد، درس، اتاق، روز و زمان را انتخاب کنید
- سیستم خودکار از تداخل جلوگیری می‌کند

### ویژگی‌های پیشرفته پنل

- **فیلتر و جستجو:** از فیلترهای سمت راست استفاده کنید
- **عملیات دسته‌ای:** چند آیتم را انتخاب و عملیات را اعمال کنید
- **صدور خروجی:** داده‌ها را Export کنید (با افزودن django-import-export)

## 📱 صفحات وبسایت

### صفحه اصلی (/)
- نمایش Hero Section با تصویر تمام صفحه
- **🔍 جستجوی سریع استاد:** 
  - جعبه جستجوی زیبا در Hero Section
  - Autocomplete هوشمند با پیشنهاد نام اساتید
  - انتخاب روز با Modal تعاملی
  - نمایش تمام کلاس‌های استاد در روز انتخابی
- بخش اطلاعات سریع

### امور کلاس‌ها (/class-affairs/)
- راهنمای استفاده
- انتخاب روز هفته

### جستجوی سریع استاد (/teacher-classes/{day}/)
- **نحوه استفاده:**
  1. در صفحه اصلی، نام استاد را در جعبه جستجو وارد کنید
  2. از لیست پیشنهادات استاد مورد نظر را انتخاب کنید
  3. روز هفته را از Modal انتخاب کنید
  4. تمام کلاس‌های آن استاد در روز انتخابی نمایش داده می‌شود
- گروه‌بندی بر اساس زمان کلاس
- نمایش جزئیات کامل هر کلاس (درس، اتاق، طبقه، ظرفیت)
- وضعیت برگزاری کلاس (برگزار می‌شود / برگزار نمی‌شود)

### انتخاب زمان (/class-affairs/{day}/)
- انتخاب زمان کلاس برای روز انتخاب شده

### نمایش طبقات (/class-affairs/{day}/{time}/)
- نمایش بصری طبقات
- اتاق‌های چپ، راست و مرکزی
- اطلاعات کامل کلاس‌ها

## 🎨 سفارشی‌سازی

### تغییر رنگ‌ها
فایل `static/css/style.css` را باز کرده و متغیرهای CSS را تغییر دهید:

```css
:root {
    --primary-blue: #1e3c72;
    --secondary-blue: #2196F3;
    --white: #ffffff;
    --black: #000000;
}
```

### تغییر تصویر Hero
تصویر `static/images/hero-bg.jpg` را با تصویر دلخواه جایگزین کنید.

### افزودن صفحات جدید
1. ویو را در `classes/views.py` اضافه کنید
2. URL را در `classes/urls.py` تعریف کنید
3. قالب را در `templates/classes/` ایجاد کنید

## 🧪 تست

برای اجرای تست‌ها:

```bash
python manage.py test classes
```

## 🔧 عیب‌یابی

### خطای اتصال به MySQL
- بررسی کنید MySQL در حال اجراست
- رمز عبور در settings.py را بررسی کنید
- دیتابیس ایجاد شده باشد

### خطای static files
```bash
python manage.py collectstatic --noinput
```

### خطای migration
```bash
python manage.py makemigrations --empty classes
python manage.py migrate --fake
```

## 📄 مجوز

این پروژه برای استفاده داخلی دانشکده هوش و مکاترونیک ایجاد شده است.

## 👥 تیم توسعه

- **Backend Developer:** Django & DRF Expert
- **Frontend Developer:** UI/UX Designer
- **Database Administrator:** MySQL Specialist

## 📞 پشتیبانی

در صورت بروز مشکل یا سوال:
- 📱 تلفن: +۹۸۹۱۰۲۲۹۴۸۷۰
- 📧 ایمیل: support@university.ac.ir

---

**نسخه:** 1.0.0  
**تاریخ به‌روزرسانی:** مهر ۱۴۰۳  
**وضعیت:** Production Ready ✅

---

## 🚀 استقرار (Deployment)

### استقرار با Docker و Arvan Cloud

این پروژه برای استقرار حرفه‌ای با استفاده از موارد زیر آماده شده است:

- **🐳 Docker & Docker Compose**: کانتینریزیشن کامل
- **☁️ Arvan Cloud Object Storage**: ذخیره‌سازی ابری فایل‌های استاتیک و مدیا
- **🌐 Hamravesh.com**: پلتفرم هاستینگ ایرانی

### راهنمای سریع استقرار

1. **پیکربندی Arvan Cloud Object Storage:**
   ```bash
   # در فایل .env تنظیم کنید:
   USE_S3_STORAGE=True
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   ```

2. **ساخت Docker Image:**
   ```bash
   docker build -t university-hub .
   ```

3. **اجرا با Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **استقرار در Hamravesh:**
   - فایل `Dockerfile` و `docker-compose.yml` آماده است
   - فایل `hamravesh.yaml` شامل پیکربندی‌های لازم
   - راهنمای کامل در `DEPLOYMENT.md` و `SETUP_GUIDE.md`

### فایل‌های استقرار

- `Dockerfile`: تصویر Docker برای production
- `docker-compose.yml`: تنظیمات سرویس‌های مورد نیاز
- `entrypoint.sh`: اسکریپت راه‌اندازی
- `.dockerignore`: فایل‌های نادیده گرفته شده در Docker
- `hamravesh.yaml`: پیکربندی Hamravesh
- `DEPLOYMENT.md`: راهنمای جامع استقرار
- `SETUP_GUIDE.md`: راهنمای کامل نصب و پیکربندی
- `env.template`: قالب متغیرهای محیطی
- `SUMMARY.md`: خلاصه تغییرات استقرار

### بررسی آمادگی استقرار

```bash
# بررسی خودکار آمادگی
python manage.py check_deployment

# بررسی امنیتی Django
python manage.py check --deploy

# اجرای اسکریپت بررسی
chmod +x scripts/deploy_check.sh
./scripts/deploy_check.sh
```

### پروژه مرجع

پیکربندی بر اساس پروژه موفق زیر انجام شده:
- **مخزن:** https://github.com/amirmokri/shahin-site
- از همین ساختار Arvan Cloud و Hamravesh استفاده می‌کند

**برای راهنمای کامل استقرار روی دامنه classyabb.ir، به فایل‌های `DEPLOYMENT_CLASSYABB.md` و `DEPLOYMENT.md` مراجعه کنید.**

---

## 🌐 دامنه پروداکشن

- **آدرس سایت:** https://classyabb.ir
- **پنل ادمین:** https://classyabb.ir/admin/
- **API:** https://classyabb.ir/api/

