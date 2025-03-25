import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from frappe.utils.file_manager import save_file
from json import loads
@frappe.whitelist()
def get_visit():
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.get_list('Visit',
			fields=["name as id", "customer as customer_name", "visit_type","date","time","employee","description"],
			order_by='date desc') or []
			make_response(success=True, data=data)
		else:
			make_response(success=False, message="Invalid User")
	except Exception as e:
		make_response(success=False, message=str(e))
@frappe.whitelist(allow_guest=True)
def add_visit():
	user_details = get_user_details()
	data: dict = loads(frappe.request.data)
	if user_details:
		visit = frappe.new_doc("Visit")
		visit.customer = data.get("customer_name")
		visit.visit_type = data.get("visit_type")
		visit.employee = user_details.get("employee")
		visit.description = data.get("description")
		visit.date = datetime.strptime(data.get("date"), "%d-%m-%Y")
		visit.time = data.get("time")
		visit.save(ignore_permissions=True)
		frappe.db.commit()
		make_response(success=True, message="Visit added successfully!", data=data)
	else:
		make_response(success=False, message="Session user not found!")
  
@frappe.whitelist()
def update_visit():
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.request.data
			if data:
				data = loads(data)
				if data.get("visit"):
					visit_checks = data.get("customer") or data.get("visit_type") or data.get("description")
					if visit_checks:
						u = frappe.get_doc("Visit", data.get("visit"))
						if user_details.employee == u.employee:
							if data.get("customer"):
								u.customer = data.get("customer")
							if data.get("description"):
								u.description = data.get("description")
							if data.get("visit_type"):
								u.visit_type = data.get("visit_type")
							u.flags.ignore_permissions = True
							u.save()
							frappe.db.commit()
							make_response(success=True, message="Visit Updated.")
						else:
							make_response(success=False, message="Visit Doesn't Belong to this Employee.")
					else:
						make_response(success=False, message="Nothing To Update!")
				else:
					make_response(success=False, message="Visit ID not Found!")
			else:
				make_response(success=False, message="Data not Found!")
		else:
			make_response(success=False, message="Invalid user!")
	except Exception as e:
		make_response(success=False, message=str(e))
		create_log("Update Profile", str(e))
  
