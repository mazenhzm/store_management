# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
import frappe

def execute(filters=None):
    # 1. تحديد الأعمدة (Columns) التي ستظهر في الشاشة
    columns = [
        {"label": "الصنف", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "المخزن", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "الرصيد الحالي", "fieldname": "balance", "fieldtype": "Float", "width": 120}
    ]

    # 2. استعلام من قاعدة البيانات لتجميع كميات المخزون الحالية
    # نقوم بعمل (SUM) لكل حركة المخزون وتجميعها حسب الصنف والمخزن
    data = frappe.db.sql("""
        SELECT 
            item, 
            warehouse, 
            SUM(actual_qty) as balance
        FROM 
            `tabStock Ledger Entry`
        GROUP BY 
            item, warehouse
        HAVING 
            SUM(actual_qty) != 0
    """, as_dict=1)

    return columns, data