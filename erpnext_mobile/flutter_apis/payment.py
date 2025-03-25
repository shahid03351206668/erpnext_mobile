import frappe
from datetime import datetime
from frappe.utils import cstr, cint, flt, getdate, pretty_date
from .main import create_log, make_response, get_user_details
from json import loads
@frappe.whitelist(allow_guest=True)
def get_payment():
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.get_list('Payment Entry',
			fields=["name as id", "party_type", "party", "status","mode_of_payment","company","payment_type","paid_amount","posting_date","remarks","paid_from","paid_to","total_allocated_amount","reference_date","reference_no"],
			 filters={
		'docstatus': 1},
			order_by='posting_date desc') or []
			make_response(success=True, data=data)
			
		else:
			make_response(success=False, message="Invalid User")
	except Exception as e:
		make_response(success=False, message=str(e))
@frappe.whitelist()
def add_payment():
	try:
		data = loads(frappe.request.data)
		if data:
			doc = frappe.new_doc("Payment Entry")
			doc.posting_date = data.get("posting_date")
			doc.payment_type = data.get("payment_type")
			doc.naming_series = data.get("naming_series")
			doc.company = data.get("company")
			doc.mode_of_payment = data.get("mode_of_payment")
			doc.party = data.get("party")
			doc.party_type = data.get("party_type")
			doc.paid_from = data.get("paid_from")
			doc.paid_to = data.get("paid_to")
			doc.paid_amount = data.get("paid_amount")
			doc.received_amount = data.get("received_amount")
			doc.remarks = data.get("remarks")
			doc.reference_no = data.get("reference_no")
			doc.reference_date = data.get("reference_date")
			doc.save(ignore_permissions=True)
			doc.submit()
			frappe.db.commit()
			frappe.response["message"] = "Payment Entry Created"
		else:
			frappe.response["message"] = "Data not found"
	except Exception as e:
		create_log("Api Failed", e)
			# doc.starts_on = datetime.strptime(
			#     data.get("starts_on"), "%d-%m-%Y %H:%M:%S"
			# )
@frappe.whitelist()
def get_party(party_type):
	try:
		user_details = get_user_details()
		if user_details:
			data = frappe.get_list(party_type, pluck="name")
			make_response(success=True, data=data)
		else:
			make_response(success=False, message="Invalid User")
	except Exception as e:
		make_response(success=False, message=str(e))