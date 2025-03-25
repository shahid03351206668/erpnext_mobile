import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate
from .main import create_log, make_response, get_user_details
from json import loads


# @frappe.whitelist()
# def get_holiday():
#     try:
#         user_details = get_user_details()
#         if user_details:
#             data = frappe.db.sql(
#                 f""" SELECT
#             hi.holiday_list_name, hi.from_date,hi.to_date,h.date,h.description
# 			from `tabHoliday List` hi inner join `tabHoliday` h on h.name = hi.parent where order by desc""",
#                 as_dict=1,
#             )
#             make_response(success=True, data=data)
#         else:
#             make_response(success=False, message="Invalid user!")
#     except Exception as e:
#         make_response(success=False, message=str(e))


# def get_holiday():
#     try:
#         user_details = get_user_details()
#         if user_details:
#             data = frappe.db.sql(
#                 f""" SELECT
#             hi.holiday_list_name, hi.from_date,hi.to_date,h.date,h.description
# 			from `tabHoliday List` hi inner join `tabHoliday` h on h.name = hi.parent where order by desc""",
#                 as_dict=1,
#             )
#             make_response(success=True, data=data)
#         else:
#             make_response(success=False, message="Invalid user!")
#     except Exception as e:
#         make_response(success=False, message=str(e))


@frappe.whitelist()
def get_holidays(limit=None):
    try:
        user_details = get_user_details()
        if user_details:
            parent_data = (
                frappe.get_list(
                    "Holiday List",
                    fields=[
                        "name as id",
                        "holiday_list_name",
                        "from_date",
                        "to_date",
                    ],
                    order_by="from_date desc",
                    page_length=cint(limit) if limit else 0,
                )
                or []
            )
            holiday = ""
            for p in parent_data:
                p["from_date"] = getdate(p["from_date"]).strftime("%d-%m-%Y")
                p["to_date"] = getdate(p["to_date"]).strftime("%d-%m-%Y")
                holiday_list = {row.get("id"): row for row in parent_data}
                holiday = "','".join(list(holiday_list.keys()))

            child_data = frappe.db.sql(
                f"""SELECT parent, idx, holiday_date, description from `tabHoliday` WHERE parent in ('{holiday}') order by idx""",
                as_dict=1,
            )
            for ch in child_data:
                ch["holiday_date"] = getdate(ch["holiday_date"]).strftime("%d-%m-%Y")
                row = holiday_list.get(ch.parent, {})
                if row:
                    if not row.get("holidays"):
                        row["holidays"] = []
                    row["holidays"].append(ch)
            make_response(success=True, data=[v for k, v in holiday_list.items()])
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
