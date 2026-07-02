# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class BranchCashTransfer(Document):
    def on_submit(self):
        """عند اعتماد المستند: ينقص من فرع ويزيد في الرئيسي"""
        self.update_treasury_ledger()

    def on_cancel(self):
        """عند إلغاء المستند: يعكس العملية تماماً"""
        self.update_treasury_ledger(cancel=True)

    def update_treasury_ledger(self, cancel=False):
        # معامل عكس العملية في حال الإلغاء
        factor = -1 if cancel else 1

        # 1. خزينة الفرع (ينقص منها المال -> سالب)
        from_amount = (self.amount) if cancel else (self.amount * -1)
        tle_from = frappe.get_doc({
            "doctype": "Treasury Ledger Entry",
            "treasury": self.from_treasury,
            "amount": from_amount,
            "voucher_no": self.name,
            "date": self.date
        })
        tle_from.insert(ignore_permissions=True)

        # 2. الخزينة الرئيسية (يزيد فيها المال -> موجب)
        to_amount = (self.amount * -1) if cancel else (self.amount)
        tle_to = frappe.get_doc({
            "doctype": "Treasury Ledger Entry",
            "treasury": self.to_treasury,
            "amount": to_amount,
            "voucher_no": self.name,
            "date": self.date
        })
        tle_to.insert(ignore_permissions=True)
