# -*- coding: utf-8 -*-
import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch1", "width": 120},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Reference"), "fieldname": "parent", "fieldtype": "Link", "options": "Daily Store Journal", "width": 160}
	]
	
	conditions = "WHERE parent.docstatus in (0, 1) AND parent.date >= %(from_date)s AND parent.date <= %(to_date)s"
	if filters.get("branch"):
		conditions += " AND parent.branch = %(branch)s"
		
	query = f"""
		SELECT 
			parent.date, parent.branch, child.description, child.amount, child.parent
		FROM 
			`tabDaily Expense` child
		JOIN 
			`tabDaily Store Journal` parent ON child.parent = parent.name
		{conditions}
		ORDER BY parent.date DESC
	"""
	data = frappe.db.sql(query, filters, as_dict=True)
	return columns, data
