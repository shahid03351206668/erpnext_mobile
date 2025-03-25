import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate
from .main import create_log, make_response, get_user_details
from frappe.utils.file_manager import save_file
from json import loads


@frappe.whitelist()
def get_attendance(filters=""):
    try:
        data = []
        user_details = get_user_details()
        try:
            filters: dict = loads(filters)
        except Exception:
            filters = filters

        if user_details:
            query_conds = ""
            startdate_object = None
            enddate_object = None
            if filters.get("start_date"):
                startdate_object = datetime.strptime(
                    filters.get("start_date"), "%Y-%m-%d"
                )
                query_conds += f""" and  DATE(time) >= '{filters.get("start_date")}' """

            if filters.get("end_date"):
                enddate_object = datetime.strptime(filters.get("end_date"), "%Y-%m-%d")
                query_conds += f""" and  DATE(time) <= '{filters.get("end_date")}' """

            # checkins = """ select time from `tabEmployee Checkin` where
            # log_type = "IN" and employee = ec.employee and DATE(time) = DATE(ec.time) Order BY time ASC limit 1"""
            # checkouts = """ select time from `tabEmployee Checkin` where
            # log_type = "OUT" and employee = ec.employee and DATE(time) = DATE(ec.time)  Order BY time DESC limit 1 """

            # main_checks = f""" select DATE(ec.time) as date, ec.employee, ({checkins}) as check_in, ({checkouts}) as check_out
            # from `tabEmployee Checkin` ec where ec.employee = '{user_details.get("employee")}' Group By DATE(ec.time), ec.employee Order By DATE(ec.time) DESC"""
            
            data = frappe.db.sql(
                f""" 
                select
                    DATE (ec.time) as date,
                    ec.employee,
                    (
                        select
                            time
                        from
                            `tabEmployee Checkin`
                        where
                            log_type = "IN"
                            and employee = ec.employee
                            and DATE (time) = DATE (ec.time)
                        Order BY
                            time ASC
                        limit
                            1
                    ) as check_in,
                    (
                        select
                            time
                        from
                            `tabEmployee Checkin`
                        where
                            log_type = "OUT"
                            and employee = ec.employee
                            and DATE (time) = DATE (ec.time)
                        Order BY
                            time DESC
                        limit
                            1
                    ) as check_out
                from
                    `tabEmployee Checkin` ec
                where
                    ec.employee = '{user_details.get("employee")}'
                    {query_conds}
                Group By
                    DATE (ec.time),
                    ec.employee
                Order By
                    DATE (ec.time) DESC """,
                as_dict=1,
            )

        Presents = len(["Present" for row in data if (row.check_in or row.check_out)])
        # _Presents = len(["Present" for row in data])

        response = {
            "Total": len(data),
            "Absent": len(data) - Presents,
            "Present": Presents,
        }
        if startdate_object and enddate_object:
            response.update(
                {"Total": (enddate_object.date() - startdate_object.date()).days + 1}
            )

        response["Absent"] = response["Total"] - response["Present"]

        frappe.response["graph"] = response
        frappe.response["data"] = data
        return
        # make_response(success=True, data=data)
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist(allow_guest=True)
def add_leaves():
    user_details = get_user_details()
    data: dict = loads(frappe.request.data)

    if user_details:
        leave_doc = frappe.new_doc("Leave Application")
        leave_doc.employee = user_details.get("employee")
        leave_doc.leave_type = data.get("leave_type")
        leave_doc.description = data.get("reason")
        leave_doc.to_date = datetime.strptime(data.get("to_date"), "%Y-%m-%d")
        leave_doc.from_date = datetime.strptime(data.get("from_date"), "%Y-%m-%d")

        if data.get("half_day"):
            leave_doc.half_day = bool(data.get("half_day"))
        leave_doc.save(ignore_permissions=True)

        frappe.db.commit()
        frappe.response["message"] = "Leave added successfully!"
        frappe.response["data"] = leave_doc
    else:
        frappe.response["message"] = "session user not found!"


@frappe.whitelist(allow_guest=True)
def add_attendence():
    try:
        data = loads(frappe.request.data)
        if data:
            user_details = get_user_details()
            doc = frappe.new_doc("Employee Checkin")
            doc.employee = user_details.get("employee")
            doc.log_type = data.get("type")
            datetime_str = f"""{data.get('date')} {data.get('time')}"""
            datetime_str = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            doc.time = datetime_str
            doc.custom_location_name = data.get("location_name")
            doc.device_id = data.get("location")
            doc.custom_latitude = data.get("latitude")
            doc.custom_longitude = data.get("longitude")
            doc.save(ignore_permissions=True)

            front_image = save_file(
                data.get("front_image").get("name"),
                data.get("front_image").get("base64"),
                "Employee Checkin",
                doc.name,
                decode=True,
                is_private=0,
                df="custom_front_image",
            )

            rear_image = save_file(
                data.get("rear_image").get("name"),
                data.get("rear_image").get("base64"),
                "Employee Checkin",
                doc.name,
                decode=True,
                is_private=0,
                df="custom_rear_image",
            )

            if rear_image.name and front_image.name:
                frappe.db.set_value(
                    "Employee Checkin",
                    doc.name,
                    {
                        "custom_rear_image": rear_image.file_url,
                        "custom_front_image": front_image.file_url,
                    },
                )
                frappe.db.commit()

            frappe.db.commit()
            frappe.response["message"] = "Attendance added"
        else:
            frappe.response["message"] = "Data not found"
    except Exception as e:
        create_log("Api Failed", e)
