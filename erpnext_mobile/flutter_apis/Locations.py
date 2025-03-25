import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from json import loads


@frappe.whitelist(allow_guest=True)
def employee_allowed_locations():
    try:
        user_details = get_user_details()
        if user_details:
            emp_id = user_details.get("employee")
            data = frappe.db.sql(
                f""" SELECT a.location_name, a.latitude, a.longitude,a.meters  FROM  `tabAttendance Location Employee` p INNER JOIN  `tabAttendance Location` a on a.name = p.parent 
				WHERE p.employee = '{emp_id}' 
				""",
                as_dict=True,
            )
            make_response(success=True, data=data)
        # for entry in data:
        # 	entry['latitude'] = flt(entry['latitude'],10)  # Adjust the precision as needed
        # 	entry['longitude'] = flt(entry['longitude'],10)
        # else:
        # make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))
