import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt
from .main import create_log, make_response, get_user_details
from json import loads
from .main import striphtml


@frappe.whitelist(allow_guest=True)
def add_task():
    data = loads(frappe.request.data)
    message = "Task created successfully!"
    if data:
        if data.get("task_id"):
            task_doc = frappe.get_doc("Task", data.get("task_id"))
            message = "Task updated successfully!"
        else:
            task_doc = frappe.new_doc("Task")

        task_doc.subject = data.get("subject")
        task_doc.project = data.get("project")
        task_doc.priority = data.get("priority")
        task_doc.description = data.get("description")
        task_doc.status = data.get("status")
        task_doc.exp_start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")
        task_doc.exp_end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d")

        task_doc.save(ignore_permissions=True)
        frappe.db.commit()

        if data.get("assign_to"):
            todo_doc = frappe.new_doc("ToDo")
            todo_doc.description = "Task assginment"
            todo_doc.allocated_to = data.get("assign_to")
            todo_doc.reference_type = "Task"
            todo_doc.reference_name = task_doc.name
            todo_doc.date = datetime.strptime(data.get("end_date"), "%Y-%m-%d")
            todo_doc.save(ignore_permissions=True)

        frappe.response["message"] = message
        frappe.response["data"] = task_doc
        return

    frappe.response["message"] = "Data not found"


@frappe.whitelist()
def get_task():
    try:
        user_details = get_user_details()
        if user_details:
            data = (
                frappe.get_list(
                    "Task",
                    fields=[
                        "name as id",
                        "project",
                        "subject",
                        "priority",
                        "issue",
                        "type",
                        "status",
                        "expected_time",
                        "progress",
                        "actual_time",
                        "description",
                        "exp_end_date",
                        "progress",
                    ],
                    order_by="creation desc",
                )
                or []
            )
            for d in data:
                d["assignments"] = (
                    frappe.get_list(
                        "ToDo",
                        fields=["name as id", "allocated_to", "assigned_by"],
                        filters={"reference_type": "Task", "reference_name": d.id},
                        order_by="creation desc",
                    )
                    or []
                )
                # Ensure description is a string before stripping HTML
                d["description"] = striphtml(d.get("description") or "")

            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))

