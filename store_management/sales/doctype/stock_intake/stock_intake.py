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
        
        for item in self.intake_items:
            found = False
            
            incoming_qty = flt(item.qty)
            incoming_price = flt(item.purchase_price) # سعر الشراء الحقيقي من المورد
            
            # البحث في مخزن الفرع لتحديث الكمية ومتوسط التكلفة
            for row in branch_doc.stock_balance:
                if row.product == item.product:
                    current_qty = flt(row.available_qty)
                    # جلب متوسط السعر الحالي المخزن في حقل التقييم (valuation_rate)
                    current_valuation = flt(row.valuation_rate) 
                    
                    # معادلة المتوسط المرجح المتحرك (Moving Average) بدقة متناهية
                    new_qty = current_qty + incoming_qty
                    if new_qty > 0:
                        new_valuation = ((current_qty * current_valuation) + (incoming_qty * incoming_price)) / new_qty
                    else:
                        new_valuation = incoming_price
                    
                    # تحديث البيانات المخزنية في سطر واحد نظيف
                    row.available_qty = new_qty
                    row.valuation_rate = new_valuation
                    
                    found = True
                    break
                    
            if not found:
                # أول دخول للمنتج في هذا المخزن
                branch_doc.append("stock_balance", {
                    "product": item.product,
                    "available_qty": incoming_qty,
                    "valuation_rate": incoming_price # التكلفة الأولى هي سعر الشراء الأول
                })
                    
        branch_doc.save(ignore_permissions=True)
        
        # إعادة النقدية للفرع عند إلغاء الفاتورة (حركة عكسية هامة جداً لسلامة رأس المال)
        total_purchase_amount = sum(flt(item.qty) * flt(item.purchase_price) for item in self.intake_items)
        if total_purchase_amount > 0:
            current_cash = frappe.db.get_value("Branch1", self.branch, "current_cash_balance") or 0.0
            new_cash_balance = current_cash + total_purchase_amount
            frappe.db.set_value("Branch1", self.branch, "current_cash_balance", new_cash_balance)