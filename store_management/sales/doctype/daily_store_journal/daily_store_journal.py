# Copyright (c) 2026, mazen and contributors
# For license information, please see license.txt

# import frappe
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt

class DailyStoreJournal(Document):
    
    def validate(self):
        """
        يتم تنفيذ هذا الحدث عند الضغط على 'Save'.
        وظيفتها: التحقق من توفر المخزون في الفرع وحساب الأرباح اليومية.
        """
        # 1. جلب مستند الفرع المحدد لقراءة مخزونه الحالي
        branch_doc = frappe.get_doc("Branch1", self.branch)
        
        total_product_sales = 0
        for item in self.products_sold:
            # البحث عن كمية المنتج المتوفرة داخل الجدول الفرعي للمخزون بالفرع
            available_qty = 0.0
            for stock_row in branch_doc.stock_balance:
                if stock_row.product == item.product:
                    available_qty = flt(stock_row.available_qty)
                    break
            
            # التحقق من كفاية المخزون
            if flt(item.qty) > available_qty:
                frappe.throw(
                    _("خطأ في المخزون: الكمية المطلوبة للمنتج ({0}) هي {1}، ولكن المتوفر في فرع {2} هو {3} فقط!")
                    .format(item.product, item.qty, self.branch, available_qty)
                )

            # حساب إجمالي السطر تلقائياً: الكمية * السعر
            item.amount = flt(item.qty) * flt(item.rate)
            total_product_sales += item.amount
        
        self.total_product_sales = total_product_sales
        
        # 1. حساب إجمالي المصروفات أولاً
        total_expenses = sum(flt(exp.amount) for exp in self.expenses)

            # 2. حساب ربح المنتجات بناءً على متوسط سعر الشراء (Valuation Rate) من مخزن الفرع
        product_profit = 0.0

        for item in self.products_sold:
            if not item.product:
                continue
                
            # جلب متوسط سعر الشراء الحالي للمنتج مباشرة من جدول مخزن الفرع الحالي (self.branch)
            # نستخدم frappe.db.get_value للحفاظ على كود نظيف وسريع وقراءة حقل valuation_rate مباشرة
            purchase_rate = frappe.db.get_value(
                "Branch Stock Item", # اسم الـ Doctype الفرعي للمخزن
                {
                    "product": item.product,
                    "parent": self.branch # جلب التكلفة الخاصة بهذا الفرع تحديداً لمنع تداخل الحسابات
                },
                "valuation_rate"
            )
            
            # تحويل القيمة إلى Float، وإذا لم توجد بضاعة مسبقة نضع 0.0 كحالة احتياطية
            purchase_rate = flt(purchase_rate) if purchase_rate else 0.0
            
            # ربح القطعة الواحدة = سعر البيع الحالي - متوسط سعر الشراء المرجح
            item_profit = flt(item.rate) - purchase_rate
            
            # إجمالي ربح المنتج = ربح القطعة * الكمية المباعة
            product_profit += (item_profit * flt(item.qty))

        # 3. صافي الربح الحقيقي = ربح المنتجات - المصروفات
        self.net_profit = product_profit - total_expenses

    def on_submit(self):
        """
        يتم تنفيذ هذا الحدث عند الضغط على 'Submit'.
        وظيفتها: الخصم الفعلي من مخزون الفرع وتحديث حسابات العملاء.
        """
        # 1. خصم الكميات المباعة مباشرة من جدول الفرع ومخزونه
        branch_doc = frappe.get_doc("Branch1", self.branch)
        for item in self.products_sold:
            for stock_row in branch_doc.stock_balance:
                if stock_row.product == item.product:
                    stock_row.available_qty = flt(stock_row.available_qty) - flt(item.qty)
                    break
        branch_doc.save(ignore_permissions=True)

        # 2. معالجة الديون الجديدة (زيادة مديونية العميل)
        for debt in self.new_debts:
            if debt.customer and debt.amount:
                current_debt = frappe.db.get_value("Customer", debt.customer, "total_debt") or 0.0
                frappe.db.set_value("Customer", debt.customer, "total_debt", current_debt + flt(debt.amount))
        
        # 3. معالجة سداد الديون (خصم مديونية العميل)
        for payment in self.debt_payments:
            if payment.customer and payment.amount:
                current_debt = frappe.db.get_value("Customer", payment.customer, "total_debt") or 0.0
                frappe.db.set_value("Customer", payment.customer, "total_debt", current_debt - flt(payment.amount))

            # 1. جلب السيولة النقدية الحالية للفرع من جدول الفروع
        current_cash = frappe.db.get_value("Branch1", self.branch, "current_cash_balance") or 0.0
        
        # 2. جلب إجمالي الديون الجديدة للعملاء في هذا اليوم من الجدول الفرعي (new_debts)
        total_customer_debts = sum(flt(d.amount) for d in self.new_debts)
        
        # 3. حساب الداخل (الإيرادات) بناءً على طلبك المحدد:
        # (مبيعات كاش + الربح الصافي بعد خصم المصروفات + الديون التي عند العملاء)
        total_inflow = flt(self.cash_sales) + total_customer_debts
        
        # 4. تحديث السيولة النقدية الجديدة في الفرع (إضافة الداخل إلى الرصيد السابق)
        new_cash_balance = current_cash + total_inflow
        
        # حفظ القيمة الجديدة مباشرة في قاعدة البيانات للفرع
        frappe.db.set_value("Branch1", self.branch, "current_cash_balance", new_cash_balance)        

    def on_cancel(self):
        """
        يتم تنفيذ هذا الحدث عند إلغاء المستند.
        وظيفتها: إعادة الكميات المخصومة وعكس مديونيات العملاء.
        """
        # 1. إعادة الكميات المباعة إلى مخزون الفرع
        branch_doc = frappe.get_doc("Branch1", self.branch)
        for item in self.products_sold:
            for stock_row in branch_doc.stock_balance:
                if stock_row.product == item.product:
                    stock_row.available_qty = flt(stock_row.available_qty) + flt(item.qty)
                    break
        branch_doc.save(ignore_permissions=True)

        # 2. إلغاء تأثير الديون الجديدة (خصمها مجدداً من العميل)
        for debt in self.new_debts:
            if debt.customer and debt.amount:
                current_debt = frappe.db.get_value("Customer", debt.customer, "total_debt") or 0.0
                frappe.db.set_value("Customer", debt.customer, "total_debt", current_debt - flt(debt.amount))
                
        # 3. إلغاء تأثير سداد الديون (إعادتها على العميل كدين متبقٍ)
        for payment in self.debt_payments:
            if payment.customer and payment.amount:
                current_debt = frappe.db.get_value("Customer", payment.customer, "total_debt") or 0.0
                frappe.db.set_value("Customer", payment.customer, "total_debt", current_debt + flt(payment.amount))