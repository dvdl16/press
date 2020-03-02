# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import requests
from frappe.model.document import Document
from press.press.doctype.agent_job.agent_job import Agent
from frappe.utils.password import get_decrypted_password
from press.press.doctype.site_activity.site_activity import log_site_activity
from frappe.frappeclient import FrappeClient
from frappe.utils import cint


class Site(Document):
	def autoname(self):
		domain = frappe.db.get_single_value("Press Settings", "domain")
		self.name = f"{self.subdomain}.{domain}"

	def validate(self):
		if not self.admin_password:
			self.admin_password = frappe.generate_hash(length=16)

	def after_insert(self):
		log_site_activity(self.name, "Create")
		self.create_agent_request()

	def create_agent_request(self):
		agent = Agent(self.server)
		agent.new_site(self)

		server = frappe.get_all(
			"Server", filters={"name": self.server}, fields=["proxy_server"], limit=1
		)[0]

		agent = Agent(server.proxy_server, server_type="Proxy Server")
		agent.new_upstream_site(self.server, self.name)

	def backup(self):
		log_site_activity(self.name, "Backup")
		frappe.get_doc({"doctype": "Site Backup", "site": self.name}).insert()

	def archive(self):
		log_site_activity(self.name, "Archive")
		agent = Agent(self.server)
		agent.archive_site(self)

		server = frappe.get_all(
			"Server", filters={"name": self.server}, fields=["proxy_server"], limit=1
		)[0]

		agent = Agent(server.proxy_server, server_type="Proxy Server")
		agent.remove_upstream_site(self.server, self.name)

	def login(self):
		log_site_activity(self.name, "Login as Administrator")
		return self.get_login_sid()

	def get_login_sid(self):
		password = get_decrypted_password("Site", self.name, "admin_password")
		response = requests.post(
			f"https://{self.name}/api/method/login",
			data={"usr": "Administrator", "pwd": password},
		)
		return response.cookies.get("sid")

	def setup_wizard_complete(self):
		password = get_decrypted_password("Site", self.name, "admin_password")
		conn = FrappeClient(
			f"https://{self.name}", username="Administrator", password=password
		)
		value = conn.get_value("System Settings", "setup_complete", "System Settings")
		return cint(value["setup_complete"])

	def update_site(self):
		log_site_activity(self.name, "Update")


def process_new_site_job_update(job):
	other_job_type = {
		"Add Site to Upstream": "New Site",
		"New Site": "Add Site to Upstream",
	}[job.job_type]

	first = job.status
	second = frappe.get_all(
		"Agent Job", fields=["status"], filters={"job_type": other_job_type, "site": job.site}
	)[0].status

	if "Success" == first == second:
		updated_status = "Active"
	elif "Failure" in (first, second):
		updated_status = "Broken"
	elif "Running" in (first, second):
		updated_status = "Installing"
	else:
		updated_status = "Pending"

	site_status = frappe.get_value("Site", job.site, "status")
	if updated_status != site_status:
		frappe.db.set_value("Site", job.site, "status", updated_status)


def process_archive_site_job_update(job):
	other_job_type = {
		"Remove Site from Upstream": "Archive Site",
		"Archive Site": "Remove Site from Upstream",
	}[job.job_type]

	first = job.status
	second = frappe.get_all(
		"Agent Job", fields=["status"], filters={"job_type": other_job_type, "site": job.site}
	)[0].status

	if "Success" == first == second:
		updated_status = "Archived"
	elif "Failure" in (first, second):
		updated_status = "Broken"
	else:
		updated_status = "Active"

	site_status = frappe.get_value("Site", job.site, "status")
	if updated_status != site_status:
		frappe.db.set_value("Site", job.site, "status", updated_status)
