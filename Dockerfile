FROM mazennn22/poultry-manager:latest

USER frappe

# 1. الدخول إلى المجلد الصحيح للـ bench داخل الحاوية الأساسية
WORKDIR /home/frappe/frappe-bench

# 2. نسخ كود تطبيقك الحالي إلى مجلد فرعي مؤقت لتفادي أي تعارض أثناء البناء
COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/store_management_tmp

# 3. تشغيل الأمر السحري الذي يأمر فرابي بتثبيت التطبيق محلياً من المجلد المؤقت وبنائه
RUN bench link-extension store_management_tmp && \
    bench setup-apps store_management && \
    bench build --app store_management
