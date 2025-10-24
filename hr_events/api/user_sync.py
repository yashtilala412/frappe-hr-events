import frappe
from hr_events.helpers.error import SlackIntegrationError
from hr_events.hr_events.doctype.user_meta.user_meta import update_user_meta
from hr_events.slack.slack_integration import SlackIntegration


@frappe.whitelist()
def sync_slack_users():
	"""
	Whitelisted method to trigger the background job.
	"""
	frappe.enqueue(
		sync_slack_users_job,
		queue="short",
		job_name="sync-slack-hr-events",
	)
	frappe.msgprint(
		frappe._("Syncing Slack users in the background. This may take a few minutes."),
		title="Syncing Started",
		indicator="green",
	)


def sync_slack_users_job():
	"""
	Background job to fetch all Slack users and map them to Frappe Employees.
	"""
	try:
		slack = SlackIntegration()
		# Use frappe.log() without the 'title' argument
		frappe.log("HR Events: Starting Slack user sync...")
		slack_users_map = slack.get_slack_users_by_email()
		frappe.log(
			f"HR Events: Found {len(slack_users_map)} users in Slack."
		)

		if not slack_users_map:
			# Use frappe.log() without the 'title' argument
			frappe.log("HR Events: No users found in Slack.")
			return

		# Get all active Frappe employees and their user_id (which is the email)
		employees = frappe.get_all(
			"Employee",
			filters={"status": "Active"},
			fields=["user_id", "employee_name"],
		)
		synced_count = 0
		for emp in employees:
			if not emp.user_id:
				continue

			# Check if the employee's email exists in the Slack map
			if emp.user_id in slack_users_map:
				slack_user = slack_users_map[emp.user_id]
				# Update the User Meta table
				update_user_meta(
					user_email=emp.user_id,
					data={
						"slack_user_id": slack_user["id"],
						"slack_username": slack_user["name"],
					},
				)
				synced_count += 1

		frappe.log(
			f"HR Events: Successfully synced {synced_count} users."
		)

	except SlackIntegrationError as e:
		frappe.log_error(message=str(e), title="HR Events Slack Sync Failed")
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="HR Events Sync Failed")