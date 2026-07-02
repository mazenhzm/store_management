// Copyright (c) 2026, mazen and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Debt Ledger"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1 // إجباري لكي يعرض كشف حساب لعميل محدد
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
