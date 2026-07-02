# -*- coding: utf-8 -*-
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch1", "width": 110},
		{"label": _("Cash Sales"), "fieldname": "cash_sales", "fieldtype": "Currency", "width": 110},
		{"label": _("Total Product Sales"), "fieldname": "total_product_sales", "fieldtype": "Currency", "width": 140},
		{"label": _("Total Expenses"), "fieldname": "total_expenses", "fieldtype": "Currency", "width": 120},
		{"label": _("Total New Debts"), "fieldname": "total_debts", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Debt Payments"), "fieldname": "total_payments", "fieldtype": "Currency", "width": 140},
		{"label": _("Net Profit"), "fieldname": "net_profit", "fieldtype": "Currency", "width": 120},
		{"label": _("Journal Reference"), "fieldname": "name", "fieldtype": "Link", "options": "Daily Store Journal", "width": 160}
	]
	
def get_data(filters):
	# بناء الشروط بناءً على الفلاتر المدخلة
	conditions = "WHERE docstatus in (0, 1) AND date >= %(from_date)s AND date <= %(to_date)s"
	if filters.get("branch"):
		conditions += " AND branch = %(branch)s"

	# تم تصحيح j.total_product_s إلى j.total_product_sales ليطابق قاعدة البيانات تماماً
	query = f"""
		SELECT 
			j.name,
			j.date,
			j.branch,
			j.cash_sales,
			j.total_product_sales as total_product_sales,
			j.net_profit,
			(SELECT COALESCE(SUM(amount), 0) FROM `tabDaily Expense` WHERE parent = j.name) as total_expenses,
			(SELECT COALESCE(SUM(amount), 0) FROM `tabDaily Debt` WHERE parent = j.name) as total_debts,
			(SELECT COALESCE(SUM(amount), 0) FROM `tabDaily Debt Payment` WHERE parent = j.name) as total_payments
		FROM 
			`tabDaily Store Journal` j
		{conditions}
		ORDER BY 
			j.date DESC
	"""
	
	return frappe.db.sql(query, filters, as_dict=True)