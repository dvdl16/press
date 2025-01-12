# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe and contributors
# For license information, please see license.txt

import calendar
import json
import secrets
from datetime import datetime

import frappe
import requests

from press.api.developer.marketplace import get_subscription_info
from press.api.site import site_config, update_config
from press.utils import log_error


class PlanExpiredError(Exception):
	http_status_code = 401


@frappe.whitelist(allow_guest=True)
def email_ping():
	return "pong"


def setup(site):
	"""
	set site config for overriding email account validations
	"""
	doc_exists = frappe.db.exists("Mail Setup", {"site": site})

	if doc_exists:
		doc = frappe.get_doc("Mail Setup", doc_exists)

		if not doc.is_complete:
			doc.is_complete = 1
			doc.save()

		return

	old_config = site_config(site)

	new_config = [
		{"key": "mail_login", "value": "example@gmail.com", "type": "String"},
		{"key": "mail_password", "value": "password", "type": "String"},
		{"key": "mail_port", "value": 587, "type": "Number"},
		{"key": "mail_server", "value": "smtp.gmail.com", "type": "String"},
	]
	for row in old_config:
		new_config.append({"key": row.key, "value": row.value, "type": row.type})

	update_config(site, json.dumps(new_config))

	frappe.get_doc({"doctype": "Mail Setup", "site": site, "is_complete": 1}).insert(
		ignore_permissions=True
	)


@frappe.whitelist(allow_guest=True)
def get_analytics(**data):
	"""
	send data for a specific month
	"""
	month = data.get("month")
	year = datetime.now().year
	last_day = calendar.monthrange(year, int(month))[1]
	status = data.get("status")
	site = data.get("site")
	subscription_key = data.get("key")

	for value in (site, subscription_key):
		if not value or not isinstance(value, str):
			frappe.throw("Invalid Request")

	result = frappe.get_all(
		"Mail Log",
		filters={
			"site": site,
			"subscription_key": subscription_key,
			"status": ["like", f"%{status}%"],
			"date": ["between", [f"{month}-01-{year}", f"{month}-{last_day}-{year}"]],
		},
		fields=["date", "status", "message", "sender", "recipient"],
		order_by="date asc",
	)

	return result


def validate_plan(secret_key):
	"""
	check if subscription is active on marketplace and valid
	#TODO: get activation date
	"""

	if not secret_key or not isinstance(secret_key, str):
		frappe.throw("Invalid Secret Key")

	if frappe.db.exists("Subscription", {"secret_key": secret_key}):
		return True

	# TODO: replace this with plan attributes
	plan_label_map = frappe.conf.email_plans

	try:
		subscription = get_subscription_info(secret_key=secret_key)
	except Exception as e:
		frappe.throw(e)

	if subscription["enabled"]:
		# TODO: add a date filter(use start date from plan)
		first_day = str(datetime.now().replace(day=1).date())
		count = frappe.db.count(
			"Mail Log",
			filters={
				"site": subscription["site"],
				"status": "delivered",
				"creation": (">=", first_day),
				"subscription_key": secret_key,
			},
		)
		if count < plan_label_map[subscription["plan"]]:
			return True
		else:
			frappe.throw(
				"Your plan for email delivery service has expired try upgrading it from, "
				f"https://frappecloud.com/dashboard/sites/{subscription['site']}/overview",
				PlanExpiredError,
			)

	return False


@frappe.whitelist(allow_guest=True)
def send_mime_mail(**data):
	"""
	send api request to mailgun
	"""
	files = frappe._dict(frappe.request.files)
	data = json.loads(data["data"])

	if validate_plan(data["sk_mail"]):
		api_key, domain = frappe.db.get_value(
			"Press Settings", None, ["mailgun_api_key", "root_domain"]
		)

		resp = requests.post(
			f"https://api.mailgun.net/v3/{domain}/messages.mime",
			auth=("api", f"{api_key}"),
			data={"to": data["recipients"], "v:sk_mail": data["sk_mail"]},
			files={"message": files["mime"].read()},
		)

		if resp.status_code == 200:
			return "Sending"

	return "Error"


@frappe.whitelist(allow_guest=True)
def event_log():
	"""
	log the webhook and forward it to site
	"""
	data = json.loads(frappe.request.data)
	event_data = data.get("event-data")

	if not event_data:
		return

	if event_data.get("user-variables", {}).get("sk_mail") is None:
		# We don't know where to send this event
		# TOOD: Investigate why this is happening
		# Hint: Likely from other emails not sent via the email delivery app
		return

	if "delivery-status" not in event_data:
		return

	if "message" not in event_data["delivery-status"]:
		return

	try:
		secret_key = event_data["user-variables"]["sk_mail"]
		headers = event_data["message"]["headers"]
		if "message-id" not in headers:
			# We can't log this event without a message-id
			# TOOD: Investigate why this is happening
			return
		message_id = headers["message-id"]
		site = (
			frappe.get_cached_value("Subscription", {"secret_key": secret_key}, "site")
			or message_id.split("@")[1]
		)
		status = event_data["event"]

		frappe.get_doc(
			{
				"doctype": "Mail Log",
				"unique_token": secrets.token_hex(25),
				"message_id": message_id,
				"sender": headers["from"],
				"recipient": event_data.get("recipient") or headers.get("to"),
				"site": site,
				"status": event_data["event"],
				"subscription_key": secret_key,
				"message": event_data["delivery-status"]["message"]
				or event_data["delivery-status"]["description"],
				"log": json.dumps(data),
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		log_error("Mail App: Event log error", data=data)
		raise

	data = {"status": status, "message_id": message_id, "secret_key": secret_key}

	try:
		host_name = frappe.db.get_value("Site", site, "host_name") or site
		requests.post(
			f"https://{host_name}/api/method/email_delivery_service.controller.update_status",
			data=data,
		)
	except Exception as e:
		log_error("Mail App: Email status update error", data=e)
		return "Successful", 200

	return "Successful", 200
