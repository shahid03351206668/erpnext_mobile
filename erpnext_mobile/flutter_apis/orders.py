import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate
from .main import create_log, make_response, get_user_details
from json import loads


@frappe.whitelist()
def get_orders(limit=None):
    try:
        user_details = get_user_details()
        if user_details:
            parent_data = (
                frappe.get_list(
                    "Sales Order",
                    fields=[
                        "name as id",
                        "transaction_date as date",
                        "customer",
                        "customer_name",
                        "status",
                        "contact_mobile",
                        "delivery_date",
                        "grand_total",
                        "grand_total as yearly_annual_billing",
                        "grand_total as total_unpaid",
                        "total_taxes_and_charges",
                        "total",
                        "discount_amount",
                    ],
                    order_by="transaction_date desc",
                    page_length=cint(limit) if limit else 0,
                )
                or []
            )

            sales_order = {row.get("id"): row for row in parent_data}
            sales_order_names = "','".join(list(sales_order.keys()))
            child_data = frappe.db.sql(
                f"""SELECT idx, parent, name as id, item_code, item_name, rate,amount,qty from `tabSales Order Item` WHERE
				parent in ('{sales_order_names}') order by idx""",
                as_dict=1,
            )
            for ch in child_data:
                row = sales_order.get(ch.parent, {})
                if row:
                    if not row.get("items"):
                        row["items"] = []
                    row["items"].append(ch)
            make_response(success=True, data=[row for name, row in sales_order.items()])
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist()
def create_order():
    try:
        user_details = get_user_details()
        if user_details:
            data = frappe.request.data
            if data:
                data = loads(data)
                so = frappe.new_doc("Sales Order")
                so.customer = data.get("customer")
                so.delivery_date = data.get("delivery_date")
                so.order_type = "Sales"
                so.company = data.get("company")
                for row in data.get("items"):
                    so.append("items", row)
                so.run_method("set_missing_values")
                so.save()
                so.submit()
                frappe.db.commit()
                make_response(success=True, data={"order_id": so.name})
            else:
                make_response(success=False, message="Data not Found!")
        else:
            make_response(success=False, message="Invalid user!")
    except Exception as e:
        make_response(success=False, message=str(e))
