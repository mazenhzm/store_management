# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class PurchaseInvoice(Document):
    def on_submit(self):
        """يشتغل هذا الكود تلقائياً عند الضغط على Submit للفاتورة"""
        self.update_stock()

    def on_cancel(self):
        """يشتغل هذا الكود إذا تم إلغاء الفاتورة لعكس الحركة"""
        self.update_stock(cancel=True)

    def update_stock(self, cancel=False):
        # المرور على كافة الأصناف الموجودة في جدول الأطفال داخل الفاتورة
        for item in self.items:
            # إذا كنا نلغي الفاتورة نضرب الكمية في -1 لعكس العملية
            qty = item.qty * -1 if cancel else item.qty
            
            # إنشاء سجل حركة مخزون تلقائي
            sle = frappe.get_doc({
                "doctype": "Stock Ledger Entry",
                "item": item.item,
                "warehouse": self.target_warehouse,
                "actual_qty": qty,
                "voucher_no": self.name,
                "date": self.date
            })
            sle.insert(ignore_permissions=True)