# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
import frappe

def execute(filters=None):
    # 1. تحديد الأعمدة لتشمل التاريخ ورقم العملية والمبلغ والحركة والتراكمي
    columns = [
        {"label": "التاريخ", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "رقم العملية", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_no", "width": 160},
        {"label": "الخزينة", "fieldname": "treasury", "fieldtype": "Link", "options": "Treasury", "width": 150},
        {"label": "الحركة (المبلغ)", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "الرصيد التراكمي", "fieldname": "running_balance", "fieldtype": "Currency", "width": 140}
    ]

    # 2. جلب العمليات مرتبة تصاعدياً بحسب التاريخ والتسلسل الزمني (بدون تجميع SUM)
    data = frappe.db.sql("""
        SELECT 
            date,
            voucher_no,
            treasury,
            amount
        FROM 
            `tabTreasury Ledger Entry`
        ORDER BY 
            date ASC, creation ASC
    """, as_dict=1)

    # 3. برمجية حساب الرصيد التراكمي (Running Balance) خطوة بخطوة
    running_balance_map = {}
    
    for row in data:
        treasury = row.get("treasury")
        
        # إذا كانت هذه أول حركة للخزينة، نبدأ من الصفر
        if treasury not in running_balance_map:
            running_balance_map[treasury] = 0.0
            
        # إضافة المبلغ الحالي للرصيد التراكمي الخاص بهذه الخزينة
        running_balance_map[treasury] += float(row.get("amount") or 0)
        
        # وضع القيمة التراكمية في السطر الحالي ليعرضها التقرير
        row["running_balance"] = running_balance_map[treasury]

    return columns, data