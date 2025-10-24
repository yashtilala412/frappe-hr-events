# Copyright (c) 2025, yashtilala and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UserMeta(Document):
	pass


def update_user_meta(user_email: str, data: dict):
	"""
	Create or update the User Meta document for a given user email.
	"""
	if not user_email:
		return

	if frappe.db.exists("User Meta", {"user": user_email}):
		doc = frappe.get_doc("User Meta", {"user": user_email})
	else:
		doc = frappe.new_doc("User Meta")
		doc.user = user_email

	doc.update(data)
	doc.save(ignore_permissions=True)
	return doc


@frappe.whitelist()
def get_slack_user_id(frappe_user_email: str) -> str | None:
	"""
	Get the Slack User ID for the given Frappe User email.
	Returns None if not found.
	"""
	if not frappe_user_email:
		return None

	slack_user_id = frappe.db.get_value(
		"User Meta",
		filters={"user": frappe_user_email},
		fieldname="slack_user_id",
	)
	return slack_user_id