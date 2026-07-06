# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	
	# حساب صف الإجمالي إذا كانت هناك بيانات متوفرة
	if data:
		total_row = calculate_totals(data)
		data.append(total_row)
		
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
	conditions = "WHERE docstatus in (0, 1) AND date >= %(from_date)s AND date <= %(to_date)s"
	if filters.get("branch"):
		conditions += " AND branch = %(branch)s"

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

def calculate_totals(data):
	# دالة ذكية للمرور على كل السطور وجمع القيم المالية لكل عمود بشكل منفصل
	total_cash_sales = 0.0
	total_product_sales = 0.0
	total_expenses = 0.0
	total_debts = 0.0
	total_payments = 0.0
	total_net_profit = 0.0
	
	for row in data:
		total_cash_sales += flt(row.get("cash_sales"))
		total_product_sales += flt(row.get("total_product_sales"))
		total_expenses += flt(row.get("total_expenses"))
		total_debts += flt(row.get("total_debts"))
		total_payments += flt(row.get("total_payments"))
		total_net_profit += flt(row.get("net_profit"))
		
	# إرجاع قاموس يمثل السطر الأخير ويحتوي على كلمة "الإجمالي" والمجاميع
	return {
		"date": _("Total / الإجمالي"),
		"cash_sales": total_cash_sales,
		"total_product_sales": total_product_sales,
		"total_expenses": total_expenses,
		"total_debts": total_debts,
		"total_payments": total_payments,
		"net_profit": total_net_profit
	}