import frappe
from frappe.utils import getdate

from hr_events.helpers.error import SlackIntegrationError
from hr_events.hr_events.doctype.user_meta.user_meta import get_slack_user_id
from hr_events.slack.slack_integration import SlackIntegration


def send_event_reminders():
	"""
	Send birthday and work anniversary reminders to employees via Slack DM.
	This function is called daily by the scheduler.
	"""
	try:
		slack = SlackIntegration()
	except SlackIntegrationError as e:
		frappe.log_error(message=str(e), title="HR Events: Failed to init Slack")
		return  # Stop if Slack isn't configured

	today = getdate()
	today_month = today.month
	today_day = today.day

	# --- Send Birthday Wishes ---
	send_birthday_wishes(slack, today_month, today_day)

	# --- Send Work Anniversary Wishes ---
	send_work_anniversary_wishes(slack, today, today_month, today_day)


def send_birthday_wishes(slack: SlackIntegration, month: int, day: int):
	"""Fetch and send birthday wishes."""
	try:
		# MODIFIED: Added `company` to the SQL query
		birthday_employees = frappe.db.sql(
			"""
			SELECT user_id, employee_name, company
			FROM `tabEmployee`
			WHERE status = 'Active'
				AND MONTH(date_of_birth) = %(month)s
				AND DAY(date_of_birth) = %(day)s
			""",
			values={"month": month, "day": day},
			as_dict=True,
		)

		for emp in birthday_employees:
			if not emp.user_id:
				continue

			slack_user_id = get_slack_user_id(emp.user_id)
			if slack_user_id:
				# MODIFIED: Get company name and add to message
				company_name = "the team"  # Default fallback
				if emp.company:
					# Get company name from the Company Doctype
					company_name = frappe.get_cached_value("Company", emp.company, "company_name")
				
				message = f"Happy Birthday, {emp.employee_name}! 🎂🎉 Best wishes on your birthday from {company_name}."
				slack.send_dm(slack_user_id, message)
				frappe.log(f"HR Events: Sent birthday wish to {emp.employee_name}")

	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(), title="HR Events: Birthday Wish Failed"
		)


def send_work_anniversary_wishes(
	slack: SlackIntegration, today: object, month: int, day: int
):
	"""Fetch and send work anniversary wishes."""
	try:
		# MODIFIED: Added `company` to the SQL query
		anniversary_employees = frappe.db.sql(
			"""
			SELECT user_id, employee_name, date_of_joining, company
			FROM `tabEmployee`
			WHERE status = 'Active'
				AND MONTH(date_of_joining) = %(month)s
				AND DAY(date_of_joining) = %(day)s
				AND date_of_joining != %(today)s
			""",
			values={"month": month, "day": day, "today": today},
			as_dict=True,
		)

		for emp in anniversary_employees:
			if not emp.user_id:
				continue

			slack_user_id = get_slack_user_id(emp.user_id)
			if slack_user_id:
				joining_date = getdate(emp.date_of_joining)
				years = today.year - joining_date.year

				suffix = "th"
				if years % 10 == 1 and years != 11:
					suffix = "st"
				elif years % 10 == 2 and years != 12:
					suffix = "nd"
				elif years % 10 == 3 and years != 13:
					suffix = "rd"

				# MODIFIED: Get company name and add to message
				company_name = "the team"  # Default fallback
				if emp.company:
					company_name = frappe.get_cached_value("Company", emp.company, "company_name")

				message = f"Happy Work Anniversary, {emp.employee_name}! 🥳 Thank you for {years}{suffix} great year(s) with {company_name}!"
				slack.send_dm(slack_user_id, message)
				frappe.log(
					f"HR Events: Sent anniversary wish to {emp.employee_name} for {years} years"
				)

	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="HR Events: Anniversary Wish Failed",
		)