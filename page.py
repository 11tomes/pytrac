#!/usr/bin/env python


from cookielib import LWPCookieJar
from urllib2 import build_opener, install_opener, HTTPCookieProcessor
from urllib import urlencode
from os.path import isfile
from re import search, DOTALL

from multipartposthandler import MultipartPostHandler
from scriptlib import printDebug, prompt
from traclib.form import TracTicketAttachmentForm, TracFormParser, TracTicketForm


TICKET_DIR = '$ticket_dir'


class TracPage(object):
	"""Represents a Trac web page (http://trac.edgewall.org/)

	"""
	#@todo: testability
	base_url = '$trac_host'
	_cookie_file = TICKET_DIR + 'trac'
	_form_data = None
	_url = None

	def __init__(self, args, path=''):
		self._args = args
		self.set_path(path)

	def _get_cookie_jar(self):
		if not hasattr(self, '_cookie_jar'):
			cj = LWPCookieJar()
			if not isfile(self._cookie_file):
				# @todo:use notifications or login?
				raise IOError('Snap! Who stole the cookie in the cookie jar?')

			cj.load(self._cookie_file)
			self._cookie_jar = cj

		return self._cookie_jar

	def _get_opener(self):
		if not hasattr(self, '_opener'):
			cj = self._get_cookie_jar()
			opener = build_opener(HTTPCookieProcessor(cj), MultipartPostHandler)
			install_opener(opener)
			self._opener = opener

		return self._opener

	def _open(self, url, form_data=None):
		printDebug(self._args, url)
		printDebug(self._args, form_data)

		opener = self._get_opener()
		page = opener.open(url, form_data)
		printDebug(self._args, page.geturl())
		printDebug(self._args, page.info())

		cookie_jar = self._get_cookie_jar()
		for index, cookie in enumerate(cookie_jar):
			printDebug(self._args, cookie)
		cookie_jar.save(self._cookie_file)

		return page

	def set_path(self, path):
		"""Set the full URL by specifying the path

		:param path:	the string that will be appended to the base_url
		"""
		self._url = ''.join([self.base_url, str(path)])

	def get_url(self):
		"""Returns the full URL of the page

		This is the function called by load() and submit_form() for getting the URL
		:raise Error	when url has not been set yet
		:return string:	URL as a string
		"""
		if not self._url:
			raise AttributeError('URL has not been set yet.')

		return self._url

	def get_form_data(self):
		"""Override to return the form data as a hashable.

		This is the function called by submit_form() for getting the URL parameters
		:return hashable:
		"""
		raise NotImplementedError('This method should be overriden by the sublcass.')

	def load(self):
		"""Load the page specified by the URL.

		URL is set by calling set_path(path). If URL is not set, an Error will be thrown.
		The return value is the same as that of urllib2.urlopen(url[, data][, timeout])
		"""
		return self._open(self.get_url())

	def submit_form(self):
		"""Submit the form data from get_form_data() to the url specified by get_url()
		
		See load() for return value
		"""
		return self._open(self.get_url(), self.get_form_data())


class TracTicketAttachmentPage(TracPage):
	"""Represents the page for attaching files to the ticket page.
	"""
	_path_prefix = 'attachment/ticket/'
	_path_suffix = '/?action=new&attachfilebutton=Attach+file'

	def __init__(self, args):
		"""*Do not* create new instance directly. Use TracTicketAttachmentPage.load_page(ticket)
		"""
		path = self._get_path(args.ticket)
		super(TracTicketAttachmentPage, self).__init__(args, path)
		self._form = TracTicketAttachmentForm(args)
		printDebug(args, path)
		printDebug(args, self.get_url())

	def _get_path(self, ticket):
		return ''.join([self._path_prefix, str(ticket), self._path_suffix])

	def _confirm_form_submission(self):
		if self._form.attachment is None:
			raise ValueError("Field 'attachment' has not been set yet.")

	def get_form_data(self):
		"""Overrides parent's get_Form_data

		"""
		return self._form.get_form_data()

	def choose_file(self, attachment):
		"""Use case for choosing the file to upload

		:param attachment string:	the path to the file
		"""
		if not isfile(attachment):
			raise IOError(' '.join([attachment, 'does not exist.']))

		attachment = open(attachment, 'rb')
		self._form.attachment = attachment

		printDebug(self._args, attachment)

	def set_description(self, description):
		"""Use case for setting the attachment description

		:param description string:	file description in 60 characters
		"""
		self._form.description = description

	def replace(self, replace=True):
		"""Use case for 'Replace existing attachment of the same name'

		"""
		self._form.replace = replace

	def add_attachment(self):
		"""Use case for the 'Add attachment button'

		Calls parent's submit_form(). This first checks if the form data is valid
		:raise Error:	when one of the required field value is not set
		"""
		self._confirm_form_submission()
		#@todo: preen
		return self.submit_form()

	@staticmethod
	def load_page(args):
		"""Load the attachment page for the given ticket

		:param ticket int:
		:return TracTicketAttachmentPage:
		"""
		#@todo: update
		attachment_page = TracTicketAttachmentPage(args)
		page = attachment_page.load()
		page_source = page.read()
		form_regex = '<form id="attachment" method="post" enctype="multipart/form-data" action="">.*?</form>'
		form_source = search(form_regex, page_source, DOTALL).group()
		printDebug(attachment_page._args, form_source)
		form_parser = TracFormParser(form_source)
		form_parser.fill_form_fields(attachment_page._form)
		printDebug(attachment_page._args, attachment_page._form)
		return attachment_page


class TracTicketPage(TracPage):

	def __init__(self, args):
		path = self._get_path(args.ticket)
		super(TracTicketPage, self).__init__(args, path)
		self._ticket_form = TracTicketForm(args)

	def get_form_data(self):
		return self._ticket_form.get_form_data()

	def _get_path(self, ticket_number):
		return '/'.join(['ticket', str(ticket_number)])

	def set_percent_complete(self, percent_complete):
		self._ticket_form.field_percent = percent_complete

	def set_development_status(self, devstatus):
		self._ticket_form.field_devstatus = devstatus

	def leave_as_assigned(self):
		self._ticket_form.action = TracTicketForm.action_options.leave
		
	def resolve_as(self, status):
		self._ticket_form.action = TracTicketForm.action_options.resolve
		self._ticket_form.action_resolve_resolve_resolution = status

	def reassign_to(self, username):
		self._ticket_form.action = TracTicketForm.action_options.reassign
		self._ticket_form.action_reassign_reassign_owner = username

	def accept(self):
		self._ticket_form.action = TracTicketForm.action_options.accept

	def set_comment(self, comment):
		self._ticket_form.comment = comment

	def submit_changes(self):
		printDebug(self._args, self._ticket_form)
		if self._args.prompt: prompt()
		return self.submit_form()

	@staticmethod
	def load_page(args):
		ticket_page = TracTicketPage(args)
		page = ticket_page.load()
		#@todo: refactor
		page_source = page.read()
		form_regex = '<form action="/ticket/' + str(args.ticket) + '" method="post" id="propertyform">.*</form>'
		form_source = search(form_regex, page_source, DOTALL).group()
		form_parser = TracFormParser(form_source)
		form_parser.fill_form_fields(ticket_page._ticket_form)
		return ticket_page


class TracWikiFormatting(object):

	@staticmethod
	def _format(text, markup):
		return ''.join([markup, text, markup])

	@staticmethod
	def bold(text):
		return TracWikiFormatting._format(text, "'''")

	@staticmethod
	def italic(text):
		return TracWikiFormatting._format(text, "''")


