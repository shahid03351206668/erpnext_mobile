import frappe
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from frappe.utils.file_manager import save_file
from json import loads


@frappe.whitelist()
def create_customer():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.request.data
            if data:
                data = loads(data)
                if data.get("name"):
                    create_log("Create Customer Data", str(data))
                    c = frappe.new_doc("Customer")
                    c.customer_name = data.get("name")
                    c.territory = data.get("territory")
                    c.custom_location = data.get("location")
                    c.email_id = data.get("email_id")
                    c.mobile_no = data.get("mobile_no")
                    c.flags.ignore_permissions = True
                    c.save()
                    if c.name and data.get("filename") and data.get("file_data"):
                        f_ = save_file(
                            f"""{c.name}-Customer-{data.get("filename")}""",
                            data.get("file_data"),
                            "Customer",
                            c.name,
                            decode=True,
                            is_private=0,
                            df="image",
                        )
                        if f_.name:
                            frappe.db.set_value(
                                "Customer", c.name, "image", f_.file_url
                            )
                    frappe.db.commit()
                    if c.name:
                        data_to_send = {"customer_id": c.name}
                        make_response(
                            success=True, message="Customer Created.", data=data_to_send
                        )
                    else:
                        make_response(success=False, message="Customer Name Not Found.")
                else:
                    make_response(
                        success=False,
                        message="Failed to Create Customer, Please Try Again!",
                    )
            else:
                make_response(success=False, message="Data not Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
        create_log("Create Customer", str(e))


@frappe.whitelist()
def update_customer():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.request.data
            if data:
                data = loads(data)
                check = frappe.db.get_value("Customer", data.get("customer_id"), "name")
                if check:
                    create_log("Update Customer Data", str(data))
                    if (
                        data.get("name")
                        or data.get("mobile_no")
                        or data.get("location")
                        or data.get("territory")
                        or data.get("email_id")
                    ):
                        c = frappe.get_doc("Customer", check)
                        if data.get("name"):
                            c.customer_name = data.get("name")
                        if data.get("territory"):
                            c.territory = data.get("territory")
                        if data.get("location"):
                            c.custom_location = data.get("location")
                        if data.get("mobile_no"):
                            c.mobile = data.get("mobile_no")
                        if data.get("email_id"):
                            c.email_id = data.get("email_id")
                        c.flags.ignore_permissions = True
                        c.save()
                        if c.name and data.get("filename") and data.get("file_data"):
                            f_ = save_file(
                                f"""{c.name}-Customer-{data.get("filename")}""",
                                data.get("file_data"),
                                "Customer",
                                c.name,
                                decode=True,
                                is_private=0,
                                df="image",
                            )
                            if f_.name:
                                frappe.db.set_value(
                                    "Customer", c.name, "image", f_.file_url
                                )
                        frappe.db.commit()
                        make_response(success=True, message="Customer Updated.")
                    else:
                        make_response(success=False, message="Nothing To Update!")
                else:
                    make_response(
                        success=False, message="Customer not found against this Id !"
                    )
            else:
                make_response(success=False, message="Data not Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
        create_log("Update Customer", str(e))


@frappe.whitelist()
def get_customers(limit=None):
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.get_list(
                "Customer",
                fields=[
                    "name as id",
                    "customer_name as name",
                    "image",
                    "custom_location",
                    "territory",
                    "email_id",
                    "mobile_no",
                ],
                order_by="creation desc",
                page_length=cint(limit) if limit else 0,
            )
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
