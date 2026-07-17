FROM mazennn22/poultry-manager:latest

USER frappe

# 1. نسخ كود تطبيقك الموجود في المستودع الحالي مباشرة إلى مجلد تطبيقات فرابي
COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/store_management

# 2. إخبار فرابي بأن التطبيق متاح ومثبت محلياً دون الحاجة لسحبه من الإنترنت
RUN bench setup-apps store_management && \
    bench build --app store_management
