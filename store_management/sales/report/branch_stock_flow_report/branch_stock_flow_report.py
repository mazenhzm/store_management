# -*- coding: utf-8 -*-
# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	""" الدالة الرئيسية لفرابيه التي تستدعي الأعمدة والبيانات """
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	""" تعريف أعمدة التقرير بدقة """
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": _("Operation Type"), "fieldname": "op_type", "fieldtype": "Data", "width": 140},
		{"label": _("Product"), "fieldname": "product", "fieldtype": "Link", "options": "Product", "width": 150},
		{"label": _("Inflow Qty (Togthea)"), "fieldname": "in_qty", "fieldtype": "Float", "width": 150},
		{"label": _("Outflow Qty (Sales)"), "fieldname": "out_qty", "fieldtype": "Float", "width": 150},
		{"label": _("Reference Document"), "fieldname": "ref_doc", "fieldtype": "Dynamic Link", "options": "op_type", "width": 180}
	]

def get_data(filters):
	""" جلب البيانات ودمجها لحساب التدفق """
	data = []
	
	# بناء شروط الفلاتر الزمنية مع تحديد حقل الجدول الرئيسي لمنع الغموض (parent.docstatus)
	conditions = "where parent.docstatus in (0, 1) and parent.date >= %(from_date)s and parent.date <= %(to_date)s"
	if filters.get("branch"):
		conditions += " and parent.branch = %(branch)s"

	# 1. جلب بيانات التغذية (Stock Intake) - حركات دخول
	intake_query = f"""
		SELECT 
			parent.date, parent.branch, 'Stock Intake' as op_type, child.product, child.qty as in_qty, 0.0 as out_qty, parent.name as ref_doc
		FROM 
			`tabStock Intake` parent
		JOIN 
			`tabStock Intake Detail` child ON child.parent = parent.name
		{conditions}
	"""
	try:
		intakes = frappe.db.sql(intake_query, filters, as_dict=True)
		data.extend(intakes)
	except Exception:
		pass

	# 2. جلب بيانات المبيعات اليومية (Daily Store Journal) - حركات خروج
	sales_query = f"""
		SELECT 
			parent.date, parent.branch, 'Daily Store Journal' as op_type, child.product, 0.0 as in_qty, child.qty as out_qty, parent.name as ref_doc
		FROM 
			`tabDaily Store Journal` parent
		JOIN 
			`tabDaily Sales Item` child ON child.parent = parent.name
		{conditions}
	"""
	try:
		sales = frappe.db.sql(sales_query, filters, as_dict=True)
		data.extend(sales)
	except Exception:
		pass

	# ترتيب البيانات يوماً بعد يوم بناءً على التاريخ
	data.sort(key=lambda x: x['date'] or '')
	
	return data