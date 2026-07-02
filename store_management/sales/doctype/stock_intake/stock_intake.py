# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class StockIntake(Document):
    
    def on_submit(self):
        """
        عند اعتماد فاتورة التغذية: يتم زيادة كمية المنتجات داخل جدول الفرع المحدد.
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

    def on_cancel(self):
        """
        في حال إلغاء فاتورة التغذية: يتم خصم الكميات التي غُذيت بالخطأ لإعادة المخزن لحالته.
        """
        branch_doc = frappe.get_doc("Branch1", self.branch)
        
        for item in self.intake_items:
            for row in branch_doc.stock_balance:
                if row.product == item.product:
                    row.available_qty = flt(row.available_qty) - flt(item.qty)
                    break
                    
        branch_doc.save(ignore_permissions=True)