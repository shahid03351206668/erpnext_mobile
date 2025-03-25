import frappe
from .main import get_user_details
import json
import re


def striphtml(data):
    p = re.compile(r"<.*?>")
    return p.sub("", data)


@frappe.whitelist()
def get_user_todo():
    user = get_user_details()
    user_email = user.get("email")
    todos = []
    if user_email:
        todos = frappe.db.sql(
            f"""SELECT 
            status, 
            description,
            name, 
            priority,
            allocated_to, 
            owner AS allocated_by,
            date,
            reference_type,
            reference_name
            FROM  `tabToDo`
            WHERE owner = '{user_email}'  OR allocated_to = '{user_email}'
            ORDER BY date DESC
            """,
            as_dict=True,
        )
        for todo in todos:
            todo["description"] = striphtml(todo.get("description"))
            # if "description" in todo and todo["description"]:
            # todo["description"] = html.unescape(
            #     frappe.utils.strip_html(todo["description"])
            # )
    frappe.response["data"] = todos


@frappe.whitelist(allow_guest=True)
def create_todo():
    data = frappe.request.data
    try:
        data = json.loads(data)
    except Exception:
        data = data

    if data:
        todo_doc = frappe.new_doc("ToDo")
        todo_doc.status = data.get("status")
        todo_doc.description = data.get("description")
        todo_doc.priority = data.get("priority")
        todo_doc.allocated_to = data.get("allocated_to")
        todo_doc.date = data.get("date")
        # todo_doc.reference_type = data.get("reference_type")
        # todo_doc.reference_name = data.get("reference_name")

        todo_doc.flags.ignore_permissions = True
        todo_doc.save()
        frappe.db.commit()

        if todo_doc.name:
            frappe.response["message"] = "Todo created successfully!"
            return

    frappe.response["message"] = "Something went wrong"


@frappe.whitelist(allow_guest=True)
def update_todo():
    data: dict = frappe.request.data
    try:
        data = json.loads(data)
    except Exception:
        data = data

    if data:
        todo_doc = frappe.get_doc("ToDo", data.get("name"))
        if todo_doc:

            # for key in data.keys():
            #     setattr(todo_doc, key, data[key])

            if data.get("status"):
                todo_doc.status = data.get("status")
            if data.get("description"):
                todo_doc.description = data.get("description")
            if data.get("priority"):
                todo_doc.priority = data.get("priority")
            if data.get("allocated_to"):
                todo_doc.allocated_to = data.get("allocated_to")
            if data.get("date"):
                todo_doc.date = data.get("date")
            # if data.get("reference_type"):
            #     todo_doc.allocated_to = data.get("reference_type")
            # if data.get("reference_name"):
            #     todo_doc.allocated_to = data.get("reference_name")

            todo_doc.flags.ignore_permissions = True
            todo_doc.save()
            frappe.db.commit()

        if todo_doc.name:
            frappe.response["message"] = "Todo update successfully!"
            return

    frappe.response["message"] = "Something went wrong"
