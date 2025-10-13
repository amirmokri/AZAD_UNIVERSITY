# 🚀 شروع اینجا - استقرار classyabb.ir

## خوش آمدید!

این پروژه برای استقرار روی دامنه **classyabb.ir** آماده شده است.

---

## 📚 مستندات موجود

### برای استقرار فوری (توصیه می‌شود):

1. **`CLASSYABB_CHECKLIST.md`** ⭐
   - چک‌لیست کامل فارسی
   - قدم به قدم
   - قابل چاپ و تیک زدن
   - **از اینجا شروع کنید!**

2. **`CLASSYABB_SETUP.md`**
   - راهنمای فارسی سریع
   - دستورات آماده
   - عیب‌یابی سریع

3. **`CLASSYABB_SUMMARY.md`**
   - خلاصه تنظیمات
   - آدرس‌های مهم
   - یادآوری‌ها

### برای جزئیات بیشتر:

4. **`DEPLOYMENT_CLASSYABB.md`**
   - راهنمای کامل انگلیسی
   - توضیحات تفصیلی
   - عیب‌یابی کامل

5. **`DEPLOYMENT.md`**
   - راهنمای عمومی
   - برای reference

---

## ⚡ شروع سریع (۵ قدم)

### ۱. Arvan Cloud
```
→ https://panel.arvancloud.ir/
→ ساخت باکت: classyabb-storage
→ دریافت Access Key و Secret Key
```

### ۲. تنظیمات محیطی
```bash
# کپی فایل
cp .env.production .env.production.local

# پر کردن مقادیر:
# - SECRET_KEY (تولید کنید!)
# - Database credentials
# - Arvan Cloud credentials
```

### ۳. بررسی
```bash
python manage.py check_deployment
```

### ۴. GitHub
```bash
git push origin main
```

### ۵. Hamravesh
```
→ https://console.hamravesh.com/
→ Create App → Docker → Connect GitHub
→ Set Environment Variables → Deploy
```

---

## 🎯 آدرس‌های نهایی

بعد از استقرار موفق:

- 🌐 **سایت:** https://classyabb.ir
- 👨‍💼 **ادمین:** https://classyabb.ir/admin/
- 🔌 **API:** https://classyabb.ir/api/

---

## ✅ چک‌لیست خیلی سریع

قبل از استقرار:
- [ ] باکت Arvan Cloud ساخته شده
- [ ] Database MySQL آماده است
- [ ] `.env.production` پر شده
- [ ] `check_deployment` پاس شده
- [ ] کد در GitHub است

---

## 📖 فایل‌های مهم

### تنظیمات:
- `env.template` - قالب متغیرها
- `.env.production` - تنظیمات classyabb.ir
- `docker-compose.yml` - تست محلی
- `Dockerfile` - برای استقرار

### مستندات:
- `CLASSYABB_CHECKLIST.md` ⭐ شروع از اینجا
- `CLASSYABB_SETUP.md` - راهنمای سریع
- `CLASSYABB_SUMMARY.md` - خلاصه
- `DEPLOYMENT_CLASSYABB.md` - کامل
- `README.md` - معرفی پروژه

---

## ❓ سوالات متداول

### کلید مخفی چطور تولید کنم؟
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### چطور محلی تست کنم؟
```bash
docker-compose up -d
```

### چطور آمادگی بررسی کنم؟
```bash
python manage.py check_deployment
```

### باکت Arvan Cloud چه نامی داشته باشد؟
```
پیشنهاد: classyabb-storage
(یا هر نام دیگری - در env.template تغییر دهید)
```

---

## 🆘 در صورت مشکل

### Static files بارگذاری نمی‌شود
```bash
hamravesh exec python manage.py collectstatic --noinput
```

### دیتابیس connect نمی‌شود
```bash
# بررسی credentials در Hamravesh
hamravesh exec python manage.py dbshell
```

### دامنه کار نمی‌کند
```bash
# بررسی DNS
nslookup classyabb.ir

# صبر کنید (۵-۳۰ دقیقه برای propagation)
```

---

## 📞 پشتیبانی

- **Arvan Cloud:** https://panel.arvancloud.ir/tickets
- **Hamravesh:** https://hamravesh.com/support

---

## 🎓 نکات مهم

⚠️ **SECRET_KEY** را حتماً تولید کنید (پیش‌فرض استفاده نکنید!)  
⚠️ **DEBUG=False** در production  
⚠️ فایل **`.env`** را در Git قرار ندهید  
⚠️ **DNS** تا ۳۰ دقیقه طول می‌کشد  
⚠️ **SSL** خودکار صادر می‌شود (کمی صبر کنید)  

---

## ✨ آماده‌اید؟

**گام ۱:** فایل `CLASSYABB_CHECKLIST.md` را باز کنید  
**گام ۲:** شروع کنید!  
**گام ۳:** لذت ببرید! 🎉  

---

**پروژه آماده استقرار است! ✅**  
**دامنه: classyabb.ir**  
**تاریخ: ۱۳ مهر ۱۴۰۳**

