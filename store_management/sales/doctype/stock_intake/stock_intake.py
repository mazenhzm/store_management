# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _ # إضافة استيراد دالة الترجمة لمنع المشاكل الصامتة

class StockIntake(Document):
    
    def on_submit(self):
        """
        عند اعتماد فاتورة التغذية: يتم زيادة كمية المنتجات داخل جدول الفرع المحدد وخصم القيمة من الكاش.
        """
        # 1. جلب مستند الفرع المراد تغذيته
        branch_doc = frappe.get_doc("Branch1", self.branch)
        
        # 2. المرور على المنتجات الموردة في الجدول الفرعي
        for item in self.intake_items:
            found = False
            
            # البحث إذا كان المنتج موجوداً مسبقاً في مخزن الفرع لزيادة كميته
            for row in branch_doc.stock_balance:
                if row.product == item.product:
                    row.available_qty = flt(row.available_qty) + flt(item.qty)
                    found = True
                    break
            
            # إذا كان المنتج جديداً ولم يدخل مخزن هذا الفرع من قبل، يتم إضافته كسطر جديد
            if not found:
                branch_doc.append("stock_balance", {
                    "product": item.product,
                    "available_qty": item.qty
                })
                
        # 3. حفظ تحديثات المخزن داخل الفرع
        branch_doc.save(ignore_permissions=True)
        
        # 4. الحساب الدقيق لإجمالي المشتريات (الكمية × سعر الشراء الحقيقي) لضمان عدم الاعتماد على حقل الإجمالي بالواجهة
        total_purchase_amount = sum(flt(item.qty) * flt(item.purchase_price) for item in self.intake_items)
        
        if total_purchase_amount > 0:
            # جلب السيولة النقدية الحالية للفرع
            current_cash = frappe.db.get_value("Branch1", self.branch, "current_cash_balance") or 0.0
            
            # تحقق مما إذا كان هناك سيولة كافية للشراء (اختياري)
            if current_cash < total_purchase_amount:
                frappe.msgprint(_("تنبيه: قيمة المشتريات تتجاوز السيولة النقدية الحالية للفرع!"))
            
            # تحديث سيولة الفرع بالنقصان
            new_cash_balance = current_cash - total_purchase_amount
            frappe.db.set_value("Branch1", self.branch, "current_cash_balance", new_cash_balance)

    def on_cancel(self):
        """
        في حال إلغاء فاتورة التغذية: يتم خصم الكميات وعكس الحركة المالية لإرجاع الكاش.
        """
        branch_doc = frappe.get_doc("Branch1", self.branch)
        
        for item in self.intake_items:
            for row in branch_doc.stock_balance:
                if row.product == item.product:
                    row.available_qty = flt(row.available_qty) - flt(item.qty)
                    break
                    
        branch_doc.save(ignore_permissions=True)
        
        # إعادة النقدية للفرع عند إلغاء الفاتورة (حركة عكسية هامة جداً لسلامة رأس المال)
        total_purchase_amount = sum(flt(item.qty) * flt(item.purchase_price) for item in self.intake_items)
        if total_purchase_amount > 0:
            current_cash = frappe.db.get_value("Branch1", self.branch, "current_cash_balance") or 0.0
            new_cash_balance = current_cash + total_purchase_amount
            frappe.db.set_value("Branch1", self.branch, "current_cash_balance", new_cash_balance)