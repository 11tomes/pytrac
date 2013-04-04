#!/usr/bin/env python


from traclib.page import TracTicketPage, TracTicketAttachmentPage, TracWikiFormatting
from traclib.form import TracTicketForm


class TracTicket(object):
	#@todo: get this value
	summary = None
	#@todo: handle this
	qa_tester = '$qatester'
	_ticket_page = None

	def __init__(self, args):
		self._args = args
		self._load_config()

	def _load_config(self):
		#@todo: and load summary as well
		pass

	def _get_ticket_page(self):
		if self._ticket_page is None:
			self._ticket_page = TracTicketPage.load_page(self._args)

		return self._ticket_page

	def _get_backport_comment(self, branch):
		backport = TracWikiFormatting.bold('backport')
		branch = TracWikiFormatting.italic(branch)
		return " ".join([backport, 'set to', branch])

	def set_in_progress(self):
		tp = self._get_ticket_page()
		tp.set_development_status(TracTicketForm.devstatus_options.in_progress)
		tp.accept()
		return tp.submit_changes()

	def set_under_review(self):
		tp = self._get_ticket_page()
		tp.set_percent_complete(100)
		tp.set_development_status(TracTicketForm.devstatus_options.under_review)
		return tp.submit_changes()

	def set_under_test(self):
		tp = self._get_ticket_page()
		tp.set_percent_complete(100)
		tp.set_development_status(TracTicketForm.devstatus_options.under_review)
		tp.reassign_to(self.qa_tester)
		return tp.submit_changes()

	def close(self, backport_branch=None):
		tp = self._get_ticket_page()
		tp.set_development_status(TracTicketForm.devstatus_options.merged)
		tp.resolve_as(TracTicketForm.status_options.fixed)
		if backport_branch:
			comment = self._get_backport_comment(backport_branch)
			tp.set_comment(comment)
		return tp.submit_changes()

	def attach_diff(self, diff_path, replace=True):
		tap = TracTicketAttachmentPage.load_page(self._args)
		tap.choose_file(diff_path)
		tap.replace(replace)
		return tap.add_attachment()

	def _get_summary(self):
		tp = self._get_ticket_page()
		return tp._ticket_form.field_summary

	summary = property(_get_summary)


