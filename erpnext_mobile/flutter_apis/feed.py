import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate, pretty_date
from .main import create_log, make_response, get_user_details
from json import loads
# from frappe.utils import pretty_date, now, add_to_date



@frappe.whitelist()
def get_feed():
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.get_list('Feed',
			fields=["owner as created_by","name as id", "post_type", "post_title","number_of_likes","number_of_comments","list_of_comments", "creation as posted"],
			order_by='creation desc') or []
			for row in data:
				row["created_by"] = frappe.db.get_value("User", row.get("created_by"), "username")
				row["posted"] = pretty_date(row["posted"])
			make_response(success=True, data=data)
			
		else:
			make_response(success=False, message="Invalid User")
	except Exception as e:
		make_response(success=False, message=str(e))
			