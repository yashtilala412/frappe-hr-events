// Copyright (c) 2025, yashtilala and contributors
// For license information, please see license.txt

frappe.ui.form.on("HR Event Settings", {
	refresh(frm) {
		// Add a custom button to trigger the Slack user sync
		frm.add_custom_button(__("Sync Slack Users"), () => {
			frappe.call({
				method: "hr_events.api.user_sync.sync_slack_users",
				callback: (r) => {
					if (r.message) {
						frappe.show_alert({
							message: __("Syncing started..."),
							indicator: "green",
						});
					}
				},
			});
		}).addClass("btn-primary");
	},
});