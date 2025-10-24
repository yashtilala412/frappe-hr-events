# Copyright (c) 2025, yashtilala and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UserMeta(Document):
	pass


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