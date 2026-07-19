# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = [
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch1", "width": 140},
        {"label": _("Initial Capital"), "fieldname": "initial_capital", "fieldtype": "Currency", "width": 130},
        {"label": _("(السيولة)"), "fieldname": "current_cash", "fieldtype": "Currency", "width": 140},
        {"label": _("(قيمة المخزون)"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 150},
        {"label": _("(ديون العملاء)"), "fieldname": "customer_debts", "fieldtype": "Currency", "width": 150},
        {"label": _("(رأس المال الحالي)"), "fieldname": "total_capital", "fieldtype": "Currency", "width": 160},
        {"label": _("(صافي النمو)"), "fieldname": "net_growth", "fieldtype": "Currency", "width": 130}
    ]
    
    data = []
    
    # 1. جلب الفروع مع سحب الجدول الابن الخاص بالمخزون تلقائياً لكل فرع
    # ملاحظة: استبدل "branch_stock_items" بالاسم البرمجي للحقل (Table Field Name) الموجود داخل Branch1 إن كان مختلفاً
    branches = frappe.get_all(
        "Branch1", 
        fields=["name", "initial_capital", "current_cash_balance"]
    )
    
    # 2. جلب قائمة المنتجات لعمل الـ For Loop عليها كما طلبت تماماً لإظهار كل المنتجات
    products = frappe.get_all("Product", fields=["name"])

    # الحلقة الأساسية لكل فرع
    for b in branches:
        stock_value = 0.0
        
        # جلب سجلات الجدول الابن المخزنية التابعة لهذا الفرع تحديداً من قاعدة البيانات
        # اسم الحقل الأب في الجداول الأبناء يكون دائماً parent
        child_items = frappe.get_all(
            "Branch Stock Item",
            filters={"parent": b.name},
            fields=["product", "available_qty", "valuation_rate"]
        )
        
        # تحويل محتويات الجدول الابن للفرع إلى قاموس سريع للبحث بداخل الذاكرة
        stock_map = {item.product: item for item in child_items}
        
        # 3. عمل For Loop على كل المنتجات وحساب قيمتها لـ رأس المال
        for p in products:
            product_entry = stock_map.get(p.name)
            
            if product_entry:
                qty = flt(product_entry.available_qty)
                rate = flt(product_entry.valuation_rate)
                
                if qty > 0:
                    stock_value += (qty * rate)

        # 4. حساب صافي ديون العملاء المتبقية التابعة للفرع
        debts_result = frappe.db.sql("""
            SELECT 
                (SELECT SUM(child.amount) FROM `tabDaily Debt` child 
                 JOIN `tabDaily Store Journal` parent ON child.parent = parent.name 
                 WHERE parent.branch = %s AND parent.docstatus = 1) as given,
                (SELECT SUM(child.amount) FROM `tabDaily Debt Payment` child 
                 JOIN `tabDaily Store Journal` parent ON child.parent = parent.name 
                 WHERE parent.branch = %s AND parent.docstatus = 1) as received
        """, (b.name, b.name), as_dict=1)
        
        total_given = flt(debts_result[0].given) if debts_result else 0.0
        total_received = flt(debts_result[0].received) if debts_result else 0.0
        customer_debts = total_given - total_received

        # 5. العمليات الحسابية الختامية المتوافقة مع واجهة تقريرك المرفق
        cash = flt(b.current_cash_balance)
        total_capital = cash + stock_value + customer_debts
        initial = flt(b.initial_capital)
        net_growth = total_capital - initial
        
        data.append({
            "branch": b.name,
            "initial_capital": initial,
            "current_cash": cash,
            "stock_value": stock_value,
            "customer_debts": customer_debts,
            "total_capital": total_capital,
            "net_growth": net_growth
        })
        
    return columns, data