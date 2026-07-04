# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch1", "width": 140},
		{"label": _("Initial Capital"), "fieldname": "initial_capital", "fieldtype": "Currency", "width": 130},
		{"label": _("Available Cash (السيولة)"), "fieldname": "current_cash", "fieldtype": "Currency", "width": 140},
		{"label": _("Stock Value (قيمة المخزون)"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 150},
		{"label": _("Customer Debts (ديون العملاء)"), "fieldname": "customer_debts", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Capital (رأس المال الحالي)"), "fieldname": "total_capital", "fieldtype": "Currency", "width": 160},
		{"label": _("Net Growth (صافي النمو)"), "fieldname": "net_growth", "fieldtype": "Currency", "width": 130}
	]
	
	data = []
	branches = frappe.get_all("Branch1", fields=["name", "initial_capital", "current_cash_balance"])
	
	for b in branches:
		# 1. حساب قيمة البضاعة المتبقية في المخزن (الداخل - الخارج) * سعر الشراء
		stock_value = 0.0
		products = frappe.get_all("Product", fields=["name"])
		for p in products:
			in_qty = frappe.db.sql("""
				SELECT SUM(child.qty) FROM `tabStock Intake Detail` child
				JOIN `tabStock Intake` parent ON child.parent = parent.name
				WHERE parent.branch = %s AND child.product = %s AND parent.docstatus = 1
			""", (b.name, p.name))[0][0] or 0.0
			
			out_qty = frappe.db.sql("""
				SELECT SUM(child.qty) FROM `tabDaily Sales Item` child
				JOIN `tabDaily Store Journal` parent ON child.parent = parent.name
				WHERE parent.branch = %s AND child.product = %s AND parent.docstatus = 1
			""", (b.name, p.name))[0][0] or 0.0
			
			current_qty = in_qty - out_qty
			
			if current_qty > 0:
				last_price = frappe.db.sql("""
					SELECT child.purchase_price FROM `tabStock Intake Detail` child
					JOIN `tabStock Intake` parent ON child.parent = parent.name
					WHERE child.product = %s AND parent.docstatus = 1
					ORDER BY parent.date DESC, parent.creation DESC LIMIT 1
				""", p.name)
				purchase_rate = flt(last_price[0][0]) if last_price else 0.0
				stock_value += (current_qty * purchase_rate)

		# 2. حساب صافي ديون العملاء المتبقية التابعة لهذا الفرع (إجمالي الديون المعطاة - إجمالي السداد المستلم)
		total_given_debts = frappe.db.sql("""
			SELECT SUM(child.amount) FROM `tabDaily Debt` child
			JOIN `tabDaily Store Journal` parent ON child.parent = parent.name
			WHERE parent.branch = %s AND parent.docstatus = 1
		""", b.name)[0][0] or 0.0

		total_received_payments = frappe.db.sql("""
			SELECT SUM(child.amount) FROM `tabDaily Debt Payment` child
			JOIN `tabDaily Store Journal` parent ON child.parent = parent.name
			WHERE parent.branch = %s AND parent.docstatus = 1
		""", b.name)[0][0] or 0.0

		customer_debts = total_given_debts - total_received_payments

		# 3. الحسابات الختامية الشاملة لرأس المال
		cash = flt(b.current_cash_balance)
		
		# رأس المال الحالي = الكاش + المخزون + الديون المتبقية عند العملاء
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