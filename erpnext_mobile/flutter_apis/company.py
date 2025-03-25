import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from json import loads
@frappe.whitelist()
def get_companies():
    data = frappe.get_list(
        "Company",
        pluck="name",
    )
    frappe.response["data"] = data