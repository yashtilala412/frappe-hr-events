# hr_events/slack/slack_integration.py

import frappe
from hr_events.helpers.error import SlackIntegrationError
from slack_bolt import App


class SlackIntegration:
	"""Handles communication with Slack using stored HR Event Settings."""

	def __init__(self):
		self.settings = self._get_settings()
		if not self.settings.get("bot_token"):
			raise SlackIntegrationError("Slack bot token is missing or invalid.")
		self.app = App(token=self.settings.get("bot_token"))

	def _get_settings(self):
		"""Fetch Slack configuration from HR Event Settings Doctype securely."""
		
		# Use frappe.get_single to get the Document object, not a dict
		settings_doc = frappe.get_single("HR Event Settings")

		if not settings_doc:
			raise SlackIntegrationError("HR Event Settings not found.")

		# 🔒 Use the .get_password() method on the document object
		bot_token = settings_doc.get_password("slack_bot_token")

		return {
			"bot_token": bot_token,
			"default_channel": settings_doc.slack_channel,
		}

	def send_dm(self, user_id: str, message: str):
		"""Send a direct message to a Slack user."""
		try:
			return self.app.client.chat_postMessage(channel=user_id, text=message)
		except Exception as e:
			frappe.log_error(
				message=f"Failed to send DM to {user_id}: {e}",
				title="Slack DM Send Failed",
			)
			# Don't raise an error, just log it.
			# We don't want a single failed DM to stop the whole scheduler.
			return None

	def get_slack_users_by_email(self, limit: int = 500) -> dict:
		"""
		Get all users from Slack and return a dictionary of email -> slack_user.
		This is used to map ERPNext users to Slack users.
		"""
		user_dict = {}
		cursor = None

		while True:
			try:
				# Make API call with cursor if it exists
				if cursor:
					result = self.app.client.users_list(limit=limit, cursor=cursor)
				else:
					result = self.app.client.users_list(limit=limit)

				users = result.get("members", [])

				for user in users:
					email = user.get("profile", {}).get("email")
					if (
						not email
						or user["deleted"]
						or user["is_bot"]
						or user["is_app_user"]
					):
						continue
					user_dict[email] = {
						"id": user["id"],
						"name": user["name"],
						"real_name": user.get("real_name"),
					}

				# Check if there are more users to fetch
				cursor = result.get("response_metadata", {}).get("next_cursor")
				if not cursor:
					break  # No more users to fetch

			except Exception as e:
				frappe.log_error(title="Error fetching Slack users", message=str(e))
				raise SlackIntegrationError(f"Error fetching Slack users: {e}")

		return user_dict