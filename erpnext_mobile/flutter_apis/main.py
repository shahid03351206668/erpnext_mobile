import frappe
from frappe.utils import cstr, cint, flt, getdate, now
from frappe.utils.file_manager import save_file

from datetime import datetime
import requests
import json
import re
from frappe.utils.file_manager import save_file


def create_log(title="App Api", message=""):
    frappe.log_error(title, message)


def make_response(success=True, message="Success", data={}, session_success=True):
    frappe.local.response["message"] = {
        "session_success": session_success,
        "success": success,
        "success_key": cint(success),
        "message": message,
        "data": data,
    }


def get_user_details(user=None):
    try:
        if not user:
            user = frappe.session.user
        if user and user not in ["Guest"]:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            # sales_person = frappe.db.get_value("Sales Person", {"user": user, "enabled": 1}, "name")
            user = frappe.get_doc("User", user)
            data = {
                "name": user.name,
                "sid": frappe.session.sid,
                "username": user.username,
                "email": user.email,
                "employee": employee,
                "user_image": user.user_image,
                # "sales_person": sales_person,
            }
            return frappe._dict(data)
        else:
            make_response(
                success=False, message="Session Not Found.", session_success=False
            )
    except Exception as e:
        create_log("API Test", f"{e}\n{frappe.get_traceback()}")
        make_response(success=False, message="Invalid login credentials!")


def get_date_time_to_use():
    dt = now()
    date, time = dt.split(" ")
    date = date.split("-")
    d = datetime.strptime(time, "%H:%M:%S.%f")
    formatted_time = d.strftime("%I:%M:%S %p")
    time = time.split(":")
    data = {
        "formatted_time": formatted_time,
        "now": dt,
        "today": getdate(),
        "year": date[0],
        "month": date[1],
        "day": date[2],
        "hour": time[0],
        "min": time[1],
        "sec": time[2],
    }
    return frappe._dict(data)


@frappe.whitelist(allow_guest=True)
def get_date_time():
    try:
        user_details = get_user_details()
        if user_details:
            dt = now()
            date, time = dt.split(" ")
            date = date.split("-")
            d = datetime.strptime(time, "%H:%M:%S.%f")
            formatted_time = d.strftime("%I:%M:%S %p")
            time = time.split(":")
            data = {
                "user_details": user_details,
                "formatted_time": formatted_time,
                "now": dt,
                "today": getdate(),
                "year": date[0],
                "month": date[1],
                "day": date[2],
                "hour": time[0],
                "min": time[1],
                "sec": time[2],
            }
            make_response(data=data)
        else:
            make_response(
                success=False, message="Session Not Found.", session_success=False
            )
    except Exception as e:
        create_log("Failed to Send Datetime", e)
        make_response(success=False, message=e)


@frappe.whitelist(allow_guest=True)
def subscribe_notifications(user_id, device_token, unsubscribe=False):
    if unsubscribe:
        subcription = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` WHERE user_id = '{user_id}' AND device_token = {frappe.db.escape(device_token)}  """
        )
        if subcription:
            frappe.delete_doc("Notifications Subscriptions", subcription[0][0])
            frappe.db.commit()
            frappe.response["message"] = "Unsubcribe successfully"
        else:
            frappe.response["message"] = f"No record found for {user_id}"

    else:
        old_subcriptions = frappe.db.sql(
            f""" SELECT name, device_token FROM `tabNotifications Subscriptions` WHERE device_token = {frappe.db.escape(device_token)}  """
        )

        if old_subcriptions:
            record = old_subcriptions[0][0]
            frappe.delete_doc("Notifications Subscriptions", record)
            frappe.db.commit()

        subscription_doc = frappe.new_doc("Notifications Subscriptions")
        subscription_doc.user_id = user_id
        subscription_doc.device_token = device_token
        subscription_doc.flags.ignore_permissions = True
        subscription_doc.save()
        frappe.db.commit()
        frappe.response["message"] = "Subcribe successfully"


def striphtml(data):
    p = re.compile(r"<.*?>")
    return p.sub("", data)


def send_notifications_users(self, method=None):
    url = "https://fcm.googleapis.com/v1/projects/employee-hub-cf56c/messages:send"
    for_user = self.for_user
    content = self.email_content
    devices = frappe.db.sql(
        f"""SELECT device_token FROM `tabNotifications Subscriptions` WHERE user_id = '{for_user}' """
    )

    fire_base_settings = frappe.get_doc(
        "ERPNext Mobile Settings", "ERPNext Mobile Settings"
    )

    if not fire_base_settings.client_id or not fire_base_settings.client_secret:
        frappe.log_error("Please set the client id and client secret in ERPNext Mobile Settings")
        return
    
    for device in devices:
        device_token = device[0]
        try:
            oauth2_url = "https://oauth2.googleapis.com/token"
            oauth2_payload = json.dumps(
                {
                    "client_id": fire_base_settings.client_id,
                    "client_secret": fire_base_settings.client_secret,
                    "refresh_token": "1//04QigEfWIN3VaCgYIARAAGAQSNwF-L9IrDuVDhBuvlueynfjjKfQmL-Z03M_n9ikeekmyjxCXa60ob-Zl-svH93jiczNchN0utc0",
                    "grant_type": "refresh_token",
                }
            )
            oauth2_response = requests.request(
                "POST",
                oauth2_url,
                headers={"Content-Type": "application/json"},
                data=oauth2_payload,
            )
            if oauth2_response.status_code == 200:
                token_res = oauth2_response.json()
                access_token = token_res.get("access_token")
                if access_token:
                    firebase_token_req = requests.request(
                        "POST",
                        url,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                        data=json.dumps(
                            {
                                "message": {
                                    "token": device_token,
                                    "notification": {
                                        "body": striphtml(content),
                                        "title": striphtml(self.subject or ""),
                                    },
                                }
                            }
                        ),
                    )
                    if firebase_token_req.status_code == 200:
                        frappe.log_error("Firebase Success notification")
        except Exception as e:
            frappe.log_error("Firbase Error", str(e))
