import frappe
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details


@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
        user_details = get_user_details()
        if user_details:
            make_response(
                success=True,
                message="Authentication success",
                data=user_details,
            )
    except Exception as e:
        create_log("API Test", f"{e}\n{frappe.get_traceback()}")
        make_response(success=False, message="Invalid login credentials!")

@frappe.whitelist(allow_guest=True)
def create_user(email, pwd, username, name=None, location=None, territory=None, phone=None):
    try:
        user_doc = frappe.new_doc("User")
        user_doc.flags.ignore_permissions = True
        user_doc.flags.ignore_mandatory = True
        user_doc.username = username
        user_doc.email = email
        user_doc.new_password = pwd
        user_doc.first_name = username
        if name:
            user_doc.first_name = name
        if phone:
            user_doc.mobile_no = phone
            user_doc.phone = phone
        if location:
            user_doc.location = location
        user_doc.send_welcome_email = 0
        user_doc.append("roles", {"role":"Customer"})
        user_doc.save()
        if user_doc.name:
            frappe.db.commit()
            make_response(success=True, message="User created")
        else:
            make_response(success=False, message="Failed to create user!")
    except Exception as e:
        make_response(success=False, message=str(e))

@frappe.whitelist()
def update_user(name=None, location=None, territory=None, phone=None):
    try:
        user_details = get_user_details()
        if user_details:
            if name or phone or location or territory:
                user_doc = frappe.get_doc("User", {"email": user_details.email})
                user_doc.flags.ignore_permissions = True
                user_doc.flags.ignore_mandatory = True
                if name:
                    user_doc.first_name = name
                if phone:
                    user_doc.mobile_no = phone
                    user_doc.phone = phone
                if location:
                    user_doc.location = location
                user_doc.save()
                frappe.db.commit()
                make_response(success=True, message="User Updated")
            else:
                make_response(success=False, message="Failed to Update user!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist(allow_guest=True)
def change_pass(old_password=None, new_password=None):
    try:
        user = frappe.session.user
        if user and user not in ["Administrator", "Guest"]:
            if old_password and new_password:
                u = frappe.get_doc("User", user)
                u.new_password = new_password
                u.save()
                make_response(success=True, message="Password Changed.")
            else:
                make_response(success=False, message="Data Missing.")
        else:
            make_response(
                success=False, message="Session Not Found.", session_success=False
            )
    except Exception as e:
        create_log("Failed to change Password", e)
        make_response(success=False, message=e)

