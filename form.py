#!/usr/bin/env python

from re import sub
from HTMLParser import HTMLParser


class TracFormFieldOptions(object):
	#@note: this works, however, we are setting the attribute property dynamically, which i think is ugly since the "developer" needs to know the name of those attributes. A sol'n would be is to show those names in the class doc
	def __init__(self, options):
		self._options = options
		for option in options:
			setattr(self, self._attr(option), option)

	def __contains__(self, option):
		return (option in self._options)
		
	def __str__(self):
		return str(self._options)

	def _attr(self, option):
		if not option:
			return 'empty'
		return option.lower().replace(' ', '_')


class TracForm(object):
	#@note: this works as well, but this could be better. An idea is to use a subclass of dict with __setitem__ overriden. This has been tried but have been reverted back
	def __init__(self, fields):
		self._fields = fields
		self.__setattr__ = self.__set_field_value__

	def __set_field_value__(self, field, value):
		fn = self._get_field_fn(field)
		if hasattr(self, fn):
			getattr(self, fn)(value)
		else:
			self._set(field, value)

	def __contains__(self, field):
		return (field in self._fields)

	def __str__(self):
		return str(self.get_form_data())

	def _get_field_fn(self, field):
		return '_set_' + field

	def _set(self, field, value):
		object.__setattr__(self, field, value)

	def _del(self, field):
		delattr(self, field)

	def get_form_data(self):
		return dict([(field, getattr(self, field)) for field in self._fields if hasattr(self, field)])


class TracFormParser(HTMLParser):

	paired_tags = ['select', 'textarea', 'option']
	_handle = False
	_current_field = None

	def __init__(self, page_source):
		HTMLParser.__init__(self)
		self._page_source = page_source

	def _get_attr_value(self, attrs, attr_name):
		value = [value for (attr, value) in attrs if attr == attr_name]
		return value and value[0]

	def _handle_select(self, attrs):
		name = self._get_attr_value(attrs, 'name')
		if name in self._form:
			self._current_field = name

	def _handle_option(self, attrs):
		selected = self._get_attr_value(attrs, 'selected')
		if selected:
			self._handle = True

	def _handle_textarea(self, attrs):
		name = self._get_attr_value(attrs, 'name')
		if name in self._form:
			self._current_field = name
			self._handle = True

	def _handle_hidden(self, attrs):
		name = self._get_attr_value(attrs, 'name')
		if name in self._form:
			value = self._get_attr_value(attrs, 'value')
			setattr(self._form, name, value or '')

	def _handle_submit(self, attrs):
		self._handle_hidden(attrs)

	def _handle_file(self, attrs):
		self._handle_hidden(attrs)

	def _handle_text(self, attrs):
		self._handle_hidden(attrs)

	def _handle_radio(self, attrs):
		checked = self._get_attr_value(attrs, 'checked')
		if checked:
			self._handle_hidden(attrs)

	def handle_data(self, data):
		if self._handle:
			#@tempfix: textareas are prepended with an extra \n, we need to remove them
			data = sub('^\n', '', data)
			setattr(self._form, self._current_field, data)
			self._handle = False
			self._current_field = None

	def handle_starttag(self, tag, attrs):
		if tag in self.paired_tags:
			fn = '_handle_' + tag
			getattr(self, fn)(attrs)

	def handle_startendtag(self, tag, attrs):
		if tag == 'input':
			name = self._get_attr_value(attrs, 'name')
			if name in self._form:
				type = self._get_attr_value(attrs, 'type')
				fn = '_handle_' + type
				getattr(self, fn)(attrs)

	def fill_form_fields(self, form):
		self._form = form
		self.feed(self._page_source)


class TracTicketAttachmentForm(TracForm):

	def __init__(self, args):
		super(TracTicketAttachmentForm, self).__init__([
			'__FORM_TOKEN',
			'attachment',
			'description',
			'action',
			'realm',
			'id'])

	def _set_description(self, description):
		self._set('description', description[:60])

	def _set_replace(self, replace):
		replace_key = 'replace'
		if replace:
			self._set(replace_key,  'on')
		elif replace_key in self._form_fields:
			self._del(replace_key)


class TracTicketForm(TracForm):

	devstatus_options = TracFormFieldOptions(('', 'Pending', 'In Progress', 'Under Review', 'Merged'))
	status_options = TracFormFieldOptions(('fixed', 'closed', 'wontfix', 'duplicate', 'worksforme'))
	action_options = TracFormFieldOptions(('leave', 'resolve', 'reassign', 'accept'))

	def __init__(self, args):
		super(TracTicketForm, self).__init__([
			'__FORM_TOKEN',
			'comment',
			'field_summary',
			'field_reporter',
			'field_description',
			'field_type',
			'field_priority',
			'field_milestone',
			'field_component',
			'field_version',
			'field_severity',
			'field_keywords',
			'field_cc',
			'field_devstatus',
			'field_parentticket',
			'field_esthours',
			'field_testticket',
			'field_hoursspent',
			'field_developer',
			'field_class',
			'field_illuminateowner',
			'field_percent',
			'field_ca',
			'field_district',
			'field_zendeskticket',
			'field_navigation',
			'field_releasenote',
			'action',
			'action_resolve_resolve_resolution',
			'action_reassign_reassign_owner',
			'ts',
			'replyto',
			'cnum',
			'submit'])

	def _set_field_devstatus(self, devstatus):
		if devstatus not in self.devstatus_options:
			raise ValueError(dev_status + ' is not a valid field_devstatus value.')

		self._set('field_devstatus', devstatus)

	def _set_action(self, action):
		if action not in self.action_options:
			raise ValueError(action + ' is not a valid action value.')

		self._set('action', action)

	def _set_action_resolve_resolve_resolution(self, status):
		if status not in self.status_options:
			raise ValueError(status + ' is not a valid action_resolve_resolve_resolution value.')

		self._set('action_resolve_resolve_resolution', status)



