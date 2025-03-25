import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from json import loads


@frappe.whitelist()
def get_projects():
    data = frappe.get_list(
        "Project",
        pluck="name",
    )
    frappe.response["data"] = data

@frappe.whitelist()
def get_users():
    data = frappe.get_list(
        "User",
        pluck="name",
    )
    frappe.response["data"] = data
