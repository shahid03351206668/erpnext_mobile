import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate
from .main import create_log, make_response, get_user_details
from json import loads
@frappe.whitelist()
def get_transactions(limit=None):
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.get_list(
				"GL Entry",
				fields=[
					"name as id",
					"posting_date",
					"debit_in_account_currency",
					"credit_in_account_currency",
					"is_cancelled",
				],
				order_by="posting_date desc",
				page_length= cint(limit) if limit else 0,
			) or []
			for row in data:
				if row.get("is_cancelled"):
					row["status"] = "Cancelled"
				else:
					row["status"] = "Submitted"
			make_response(success=True, data=data)
		else:
			make_response(success=False, message="Invalid user!")
	except Exception as e:
		make_response(success=False, message=str(e))
	# try:
	# 	user_details = get_user_details()
	# 	if user_details:
	# 		data = frappe.db.sql(f"""
    #         SELECT posting_date,debit_in_account_currency,credit_in_account_currency from `tabGL Entry` where party_type = 'Customer'
    #         """,as_dict=1)
	# 		make_response(success=True, data=data)
	# 	else:
	# 		make_response(success=False, message="Invalid user!")
	# except Exception as e:
	# 	make_response(success=False, message=str(e))
