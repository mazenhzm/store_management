# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	if not filters.get("customer"):
		return [], []
		
	columns = [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Operation Type"), "fieldname": "op_type", "fieldtype": "Data", "width": 140},
		{"label": _("Debit (New Debt)"), "fieldname": "debit", "fieldtype": "Currency", "width": 130},
		{"label": _("Credit (Payment)"), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
		{"label": _("Balance Total"), "fieldname": "balance", "fieldtype": "Currency", "width": 150},
		{"label": _("Reference"), "fieldname": "parent", "fieldtype": "Link", "options": "Daily Store Journal", "width": 160}
	]
	
	all_operations = []
	conditions = "WHERE child.customer = %(customer)s AND parent.docstatus in (0, 1)"
	
	if filters.get("from_date"): conditions += " AND parent.date >= %(from_date)s"
	if filters.get("to_date"): conditions += " AND parent.date <= %(to_date)s"

	# 1. جلب حركات الديون الجديدة (تزيد المديونية - Debit)
	debt_query = f"""
		SELECT parent.date, 'New Debt' as op_type, child.amount as debit, 0.0 as credit, child.parent
		FROM `tabDaily Debt` child
		JOIN `tabDaily Store Journal` parent ON child.parent = parent.name
		{conditions}
	"""
	all_operations.extend(frappe.db.sql(debt_query, filters, as_dict=True))

	# 2. جلب حركات سداد الديون (تقلل المديونية - Credit)
	payment_query = f"""
		SELECT parent.date, 'Debt Payment' as op_type, 0.0 as debit, child.amount as credit, child.parent
		FROM `tabDaily Debt Payment` child
		JOIN `tabDaily Store Journal` parent ON child.parent = parent.name
		{conditions}
	"""
	all_operations.extend(frappe.db.sql(payment_query, filters, as_dict=True))

	# ترتيب كل العمليات تاريخياً من الأقدم للأحدث لضبط حساب المتراكم
	all_operations.sort(key=lambda x: x['date'] or '')

	# 3. الخوارزمية الذكية لحساب الرصيد المتراكم سطر بسطر (Running Total)
	running_balance = 0.0
	for op in all_operations:
		running_balance += flt(op['debit']) - flt(op['credit'])
		op['balance'] = running_balance

	return columns, all_operations