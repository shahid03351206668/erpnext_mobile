import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from json import loads


def get_expenses_data():
    try:
        user_details = get_user_details()
        if user_details:
            parent_data = (
                frappe.get_list(
                    "Expense Claim",
                    fields=[
                        "name as id",
                        "employee",
                        "status",
                    ],
                    filters={"employee": user_details.get("employee")},
                    order_by="creation desc",
                )
                or []
            )
            if parent_data:
                expense_claim = {row.get("id"): row for row in parent_data}
                expense_detail = "','".join(list(expense_claim.keys()))
                expense_details_data = frappe.db.sql(
                    f"""SELECT idx, parent, expense_date, expense_type,
					description, amount from `tabExpense Claim Detail` WHERE 
					parent in ('{expense_detail}') order by idx""",
                    as_dict=1,
                    # debug=1,
                )
                for ch in expense_details_data:
                    row = expense_claim.get(ch.parent, {})
                    if row:
                        if not row.get("expense_details"):
                            row["expense_details"] = []
                        row["expense_details"].append(ch)

                return [row for name, row in expense_claim.items()]
        else:
            return []
    except Exception:
        return []


@frappe.whitelist()
def get_leaves():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.db.sql(
                f""" select
                                leave_type,
                                employee_name,
                                status,
                                from_date,
                                to_date
                           from `tabLeave Application`
                          where employee =  '{user_details.get("employee")}'
                          order by creation desc
                           """,
                as_dict=True,
            )
            # data = (
            #     frappe.get_list(
            #         "Leave Application",
            #         fields=[
            #             "leave_type",
            #             "employee_name",
            #             "status",
            #             "from_date",
            #             "to_date",
            #         ],
            #         order_by="creation desc",
            #     )
            #     or []
            # )
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))


import random


@frappe.whitelist()
def get_leaves_and_expenses():
    try:
        user_details = get_user_details()
        if user_details:
            data = []
            leaves = (
                frappe.get_list(
                    "Leave Application",
                    fields=[
                        "name",
                        "leave_type",
                        "employee_name",
                        "status",
                        "from_date",
                        "to_date",
                    ],
                    order_by="creation desc",
                )
                or []
            )
            for i in leaves:
                i["type"] = "leaves"
                i["pdf_url"] = (
                    f"/api/method/frappe.utils.print_format.download_pdf?doctype=Leave%20Application&name={i.name}&format=Standard&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en"
                )
                i["redirect_url"] = f"/app/print/Leave%20Application/{i.name}"

            expenses = get_expenses_data()
            for j in expenses:
                j["type"] = "expenses"
                j["redirect_url"] = f"/app/print/Expense%20Claim/{i.id}"
                j["pdf_url"] = f"/api/method/frappe.utils.print_format.download_pdf?doctype=Expense%20Claim&name={i.id}&format=Standard&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en"

            data.extend(expenses)
            data.extend(leaves)

            random.shuffle(data)
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))


# @frappe.whitelist()
# def create_leave(data):
# 	create_log("Create Store", f"data: {data}")
# 	try:
# 		user_details = get_user_details()
# 		if user_details:
# 			data = loads(data)
# 			leave = frappe.new_doc("Leave Application")
# 			leave.leave_type = data.get("leave_type")
# 			leave.employee_name = data.get("employee_name")
# 			leave.status = data.get("status")
# 			leave.save()
# 			leave.submit()
# 			frappe.db.commit()
# 			make_response(success=True, data=data)
# 		else:
# 			make_response(success=False,message = "Invalid User")
# 	except Exception as e:
# 		make_response(make_response(success=False, message=str(e)))
