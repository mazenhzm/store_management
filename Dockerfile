FROM mazennn22/poultry-manager:latest

USER frappe

# سحب وتثبيت تطبيقك مباشرة فوق صورتك الجاهزة في ثوانٍ
RUN bench get-app --branch main store_management https://github.com/mazenhzm/store_management.git && \
    bench build --app store_management
