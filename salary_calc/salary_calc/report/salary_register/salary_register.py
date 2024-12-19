# Copyright (c) 2024, allen.xu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, flt


def execute(filters=None):
	columns, data = [], []
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def get_data(filters):
	conditions = get_conditions(filters,True)
	salary_query = f"""
		select
			e.name as employee,
			e.employee_name,
			e.department,
			e.company,
			sum(amount) as amount
		from
			`tabEmployee` as e
		left join
			`tabEmployee Salary Component` as es on es.parent = e.employee
		where
			e.date_of_joining < '{filters.get('from_date')}'
			{conditions}
		group by
			e.name
	"""
	employee_salary = frappe.db.sql(salary_query, as_dict=1)
	conditions = get_conditions(filters)
	att_query = f"""
		select
			e.name as employee,
			al.expected_attendance_days,
			al.attendance_days
		from
			`tabAttendance Log` al, `tabEmployee` e
		where
			al.docstatus = 1
			and al.employee = e.name
			{conditions}
	"""
	att = frappe.db.sql(att_query, as_dict=1)

	att_dict = {record['employee']: record for record in att}

	for d in employee_salary:
		attendance_rate = 0
		if att_dict.get(d.employee) and att_dict[d.employee].get('expected_attendance_days'):
			attendance_rate = round(att_dict[d.employee].get('attendance_days') / att_dict[d.employee].get('expected_attendance_days'), 3) * 100

			d.update({
				'attendance_rate': attendance_rate,
				'total_salary': flt(d.amount) * attendance_rate / 100,
				'expected_attendance_days': att_dict[d.employee].get('expected_attendance_days'),
				'attendance_days': att_dict[d.employee].get('attendance_days'),
			})

	return employee_salary

def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 200,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 240,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 240,
		},
		{
			"label": _("Expected Attendance Days"),
			"fieldname": "expected_attendance_days",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Attendance Days"),
			"fieldname": "attendance_days",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Salary"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Total Salary"),
			"fieldname": "total_salary",
			"fieldtype": "Currency",
			"width": 120,
		},
	]

def get_conditions(filters,for_employee=None):
	(start, end) = get_date(filters)
	if for_employee:
		conditions = ''
	else:
		conditions = " and al.attendance_date between '{}' and '{}'".format(start, end)
	if filters.get('employee'):
		conditions += " and e.name = '%s'" % filters.get('employee')
	if filters.get('department'):
		conditions += " and e.department = '%s'" % filters.get('department')
	if filters.get('company'):
		conditions += " and e.company = '%s'" % filters.get('company')
	return conditions


def get_date(filters):
	if not filters.get('from_date') or not filters.get('to_date'):
		frappe.throw("请设置开始和结束日期")
	start = get_datetime(filters.get('from_date')).replace(day=1)
	current_month = get_datetime(filters.get('to_date')).month
	if current_month == 12:
		next_month = 1
	else:
		next_month = current_month + 1
	
	end = add_days(get_datetime(filters.get('to_date')).replace(day=1,month=next_month),-1)
	return start, end