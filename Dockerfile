FROM mazennn22/poultry-manager:latest

USER root

COPY . /home/frappe/frappe-bench/apps/store_management

RUN chown -R frappe:frappe /home/frappe/frappe-bench/apps/store_management

USER frappe

RUN bench build --app store_management
