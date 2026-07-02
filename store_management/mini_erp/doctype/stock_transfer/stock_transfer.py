# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class StockTransfer(Document):
    def validate(self):
        """
        يتم تنفيذ هذا الحدث عند الحفظ للتأكد من توفر الكميات وحساب الأرباح.
        """
        # جلب اسم المستودع المرتبط بالفرع
        warehouse_name = frappe.db.get_value("Branch", self.branch, "warehouse") or self.branch
        
        #total_product_sales = 0
        for item in self.products_sold:
            # 1. التحقق من توفر الكمية في المخزن الحالي (مستودع الفرع)
            # نستخدم دالة get_balance_qty المدمجة في فراپي للحصول على الرصيد الحالي
            from frappe.utils import flt
            
            # جلب الكمية المتوفرة حالياً في هذا المستودع لهذا المنتج
            actual_qty = frappe.db.get_value("Bin", {"item_code": item.product, "warehouse": warehouse_name}, "actual_qty") or 0.0
            
            if flt(item.qty) > flt(actual_qty):
                # إرجاع خطأ للمستخدم ومنع الحفظ تماماً
                frappe.throw(
                    _("خطأ في المخزون: الكمية المطلوبة للمنتج ({0}) هي {1}، ولكن المتوفر في مستودع {2} هو {3} فقط!")
                    .format(item.product, item.qty, warehouse_name, actual_qty)
                )

            # حساب إجمالي السطر تلقائياً
            item.amount = flt(item.qty) * flt(item.rate)
            total_product_sales += item.amount
        
        self.total_product_sales = total_product_sales
        
        # حساب إجمالي المصروفات وصافي الربح
        total_expenses = sum(flt(exp.amount) for exp in self.expenses)
        self.net_profit = (flt(self.cash_sales) + flt(self.total_product_sales)) - total_expenses

    def on_submit(self):
        self.update_stock()

    def on_cancel(self):
        self.update_stock(cancel=True)

    def update_stock(self, cancel=False):
        for item in self.items:
            # 1. المخزن المصدر (ينقص منه المخزون، لذا نضربه في -1)
            qty_from = (item.qty) if cancel else (item.qty * -1)
            sle_from = frappe.get_doc({
                "doctype": "Stock Ledger Entry",
                "item": item.item,
                "warehouse": self.from_warehouse,
                "actual_qty": qty_from,
                "voucher_no": self.name,
                "date": self.date
            })
            sle_from.insert(ignore_permissions=True)

            # 2. المخزن المستهدف (يزيد فيه المخزون)
            qty_to = (item.qty * -1) if cancel else (item.qty)
            sle_to = frappe.get_doc({
                "doctype": "Stock Ledger Entry",
                "item": item.item,
                "warehouse": self.to_warehouse,
                "actual_qty": qty_to,
                "voucher_no": self.name,
                "date": self.date
            })
            sle_to.insert(ignore_permissions=True)
