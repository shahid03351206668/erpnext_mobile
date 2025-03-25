import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate
from .main import create_log, make_response, get_user_details
from frappe.utils.file_manager import save_file
from json import loads


@frappe.whitelist()
def get_profile_data():
    try:
        user_details = get_user_details()
        if user_details:
            data = (
                frappe.db.get_value(
                    "Employee",
                    {user_details.get("employee")},
                    [
                        "employee",
                        "date_of_joining",
                        "date_of_birth",
                        "gender",
                        "designation",
                        "emergency_phone_number",
                        "personal_email",
                        "company_email",
                        "cell_number",
                    ],
                    as_dict=1,
                )
                or {}
            )
            data.update(user_details)
            data["designation"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "designation"
            )
            data.update(user_details)
            data["gender"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "gender"
            )
            data["date_of_birth"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "date_of_birth"
            )
            data["emergency_phone_number"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "emergency_phone_number"
            )
            data["personal_email"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "personal_email"
            )
            data["company_email"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "company_email"
            )
            data["date_of_joining"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "date_of_joining"
            )
            data["cell_number"] = frappe.db.get_value(
                "Employee", user_details.get("employee"), "cell_number"
            )
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist()
def update_profile():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.request.data
            if data:
                data = loads(data)
                usr_check = (
                    data.get("cell_number")
                    or data.get("username")
                    or data.get("gender")
                    or data.get("date_of_birth")
                )
                emp_check = (
                    data.get("employee")
                    or data.get("cell_number")
                    or data.get("username")
                    or data.get("date_of_birth")
                    or data.get("date_of_joining")
                    or data.get("status")
                    or data.get("designation")
                    or data.get("gender")
                    or data.get("company_email")
                    or data.get("personal_email")
                    or data.get("emergency_phone_number")
                )
                emp = frappe.db.get_value(
                    "Employee", user_details.get("employee"), "name"
                )
                if usr_check or emp_check:
                    if user_details.name and usr_check:
                        u = frappe.get_doc("User", user_details.name)
                        # if data.get("mobile_no"):
                        #     u.mobile_no = data.get("mobile_no")
                        if data.get("gender"):
                            u.gender = data.get("gender")
                        # if data.get("company_email") or data.get("personal_email"):
                        # 	u.email = data.get("company_email") or data.get("personal_email")
                        if data.get("date_of_birth"):
                            u.birth_date = data.get("date_of_birth")
                        if data.get("username"):
                            u.username = data.get("username")
                            u.first_name = data.get("username")
                            ...
                        u.flags.ignore_permissions = True
                        u.save()

                        if data.get("user_image"):
                            request_data = data.get("user_image")
                            user_image = save_file(
                                request_data.get("name"),
                                request_data.get("base64"),
                                "User",
                                u.name,
                                decode=True,
                                is_private=0,
                                df="user_image",
                            )
                            if user_image.name:
                                frappe.db.set_value(
                                    "User", u.name, {"user_image": user_image.file_url}
                                )

                    if emp and emp_check:
                        e = frappe.get_doc("Employee", emp)
                        if data.get("cell_number"):
                            e.cell_number = data.get("cell_number")
                        if data.get("username"):
                            e.first_name = data.get("username")
                        if data.get("gender"):
                            e.gender = data.get("gender")
                        if data.get("emergency_phone_number"):
                            e.emergency_phone_number = data.get(
                                "emergency_phone_number"
                            )
                        if data.get("company_email"):
                            e.company_email = data.get("company_email")
                        if data.get("personal_email"):
                            e.personal_email = data.get("personal_email")
                        if data.get("date_of_birth"):
                            e.date_of_birth = data.get("date_of_birth")
                        if data.get("date_of_joining"):
                            e.date_of_joining = data.get("date_of_joining")
                        if data.get("status"):
                            e.status = data.get("status")
                        if data.get("designation"):
                            e.designation = data.get("designation")
                        e.flags.ignore_permissions = True
                        e.save()
                    frappe.db.commit()
                    make_response(success=True, message="Profile Updated.")
                else:
                    make_response(success=False, message="Nothing To Update!")
            else:
                make_response(success=False, message="Data not Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
        create_log("Update Profile", str(e))
