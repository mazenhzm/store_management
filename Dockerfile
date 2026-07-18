FROM mazennn22/poultry-manager:latest

USER frappe

# 1. إنشاء المجلد الفعلي للتطبيق داخل مسار تطبيقات فرابي بدقة
WORKDIR /home/frappe/frappe-bench/apps/store_management

# 2. نسخ كود تطبيقك الحالي بالكامل مباشرة إلى داخل هذا المجلد
COPY --chown=frappe:frappe . .

# 3. العودة لمجلد الـ bench الرئيسي لتسجيل وبناء التطبيق
WORKDIR /home/frappe/frappe-bench

# 4. إضافة اسم التطبيق لملف السجل الخاص بفرابي يدوياً، ثم بناء الأصول (Assets)
RUN echo "store_management" >> sites/apps.txt && \
    bench build --app store_management
