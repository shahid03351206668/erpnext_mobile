import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate, pretty_date
from .main import create_log, make_response, get_user_details
from json import loads
# @frappe.whitelist()
# def get_payroll():
# 	try:
# 		user_details = get_user_details()
# 		if user_details:
# 			data = frappe.get_list('Salary Slip',
# 			fields = ["name as id", "gross_pay", "employee","total_working_days","total_income_tax" ],
# 			order_by='creation desc') or []
# 			make_response(success=True, data=data)
# 		else:
# 			make_response(success=False, message="Invalid User")
# 	except Exception as e:
# 		make_response(success=False, message=str(e))

@frappe.whitelist()
def get_salary_slips(limit=None):
	try:
		user_details = get_user_details()
		if user_details:
			parent_data = (
				frappe.get_list(
					"Salary Slip",
					fields=[
						"name as id",
						"gross_pay",
						"employee",
						"total_working_days",
						"total_income_tax",
						"posting_date",
					],
					filters={"employee": user_details.get('employee')},
					order_by="posting_date desc",
					page_length=cint(limit) if limit else 0,
				)
				or []
			)
			if parent_data:
				salary_slip = {row.get("id"): row for row in parent_data}
				salary_slip_detail = "','".join(list(salary_slip.keys()))
				earnings_data = frappe.db.sql(
					f"""SELECT idx, parent, amount, salary_component, parentfield from `tabSalary Detail` WHERE parentfield = 'earnings' and 
					parent in ('{salary_slip_detail}') order by idx""",
					as_dict=1,
				)
				deductions_data = frappe.db.sql(
					f"""SELECT idx, parent, amount,salary_component, parentfield from `tabSalary Detail` WHERE parentfield = 'deductions' and 
					parent in ('{salary_slip_detail}') order by idx""",
					as_dict=1,
				)
				for ch in earnings_data:
					row = salary_slip.get(ch.parent, {})
					if row:
						if not row.get("earnings"):
							row["earnings"] = []
						row["earnings"].append(ch)
				for ch in deductions_data:
					row = salary_slip.get(ch.parent, {})
					if row:
						if not row.get("deductions"):
							row["deductions"] = []
						row["deductions"].append(ch)
				make_response(success=True, data=[row for name, row in salary_slip.items()])
			else:
				make_response(success=False, message="No Salary Slips Found!")
		else:
			make_response(success=False, message="Invalid user!")
	except Exception as e:
		make_response(success=False, message=str(e))
		 