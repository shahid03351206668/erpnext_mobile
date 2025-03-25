import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate, pretty_date
from .main import create_log, make_response, get_user_details
from json import loads


@frappe.whitelist()
def get_items():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.get_list(
                "Item",
                fields=[
                    "item_code",
                    "item_name",
                    "item_group",
                    "stock_uom",
                    "valuation_rate",
                    "description",
                ],
                order_by="creation desc",
            )
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))
