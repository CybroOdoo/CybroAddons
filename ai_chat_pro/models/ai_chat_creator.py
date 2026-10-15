# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json
import logging
import re
from datetime import datetime

import pytz
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import str2bool
from odoo.fields import Command, Domain
from odoo.tools.misc import format_amount, format_date, format_datetime, formatLang

from .ai_chat_assistant import (
    CLEAR_WINNER_RATIO, EXCLUDED_MODEL_PREFIXES, MAX_LIMIT, SKIPPED_FIELD_NAMES, SKIPPED_FIELD_PREFIXES,
    SKIPPED_FIELD_TYPES, STOPWORDS,
    _keywords, _mentions, _similar, _stem, _words,
)

_logger = logging.getLogger(__name__)

# fields of a model, and of its lines, proposed to the AI
MAX_CREATE_FIELDS = 40
MAX_LINE_FIELDS = 12
MAX_LINE_FIELDS_PER_RECORD = 3
MAX_SELECTION_OPTIONS = 30
MAX_LINES = 50
MAX_TEXT_LENGTH = 2000
# records a request can ask to create before the one it asks for (a new customer, new products)
MAX_NEW_RECORDS = 5
# records offered to choose among, when several match a name of the request
MAX_CHOICES = 5
# dates and times written in figures, to check the dates the AI read are in the request (dates written in
# words are checked by the words the AI quotes for them)
DATE_HINT_RE = re.compile(
    r"\b\d{1,4}[-/]\d{1,2}(?:[-/]\d{2,4})?\b|\b\d{1,2}\.\d{1,2}\.\d{2,4}\b|\b\d{1,2}:\d{2}\b",
)
# values the AI may read from words of the request ("two", "tomorrow", "yes"), checked by the words it quotes:
# a few words saying the value, not a sentence of the request
QUOTED_TYPES = ('integer', 'float', 'monetary', 'date', 'datetime', 'boolean', 'selection')
MAX_QUOTED_WORDS = 4
# fields users never set by talking
SKIPPED_CREATE_FIELDS = {'active', 'sequence', 'color', 'priority_sequence', 'company_id', 'currency_id'}
CLOSING = {'{': '}', '[': ']'}


def _read_numbers(text):
    """ The numbers a text writes, with their thousands separators ("1,450.00",
    "1,23,456.50", "1.450,00") or a decimal comma ("3,5"): every reading of each,
    as a separator alone does not tell which it is. """
    numbers = set()
    for token in re.findall(r'\d+(?:[.,]\d+)*', text or ''):
        readings = {token.replace(',', '.')} if token.count(',') + token.count('.') <= 1 else set()
        if ',' in token and '.' in token:
            # the last separator is the decimal one
            decimal = max(token.rfind(','), token.rfind('.'))
            readings.add(re.sub(r'[.,]', '', token[:decimal]) + '.' + token[decimal + 1:])
        else:
            # thousands separators only ("1,450", "1.450.000")
            readings.add(re.sub(r'[.,]', '', token))
        for reading in readings:
            try:
                numbers.add(float(reading))
            except ValueError:
                continue
    return numbers


class _Grounding:
    """ Whether the values an AI read from a request are in that request. """

    def __init__(self, env, request, spoken=()):
        self.env = env
        self.text = (request or '').lower()
        # the numbers and dates the request writes in words, as the agent read them apart
        self.spoken = [str(words).strip().lower() for words in spoken if str(words).strip()]
        self.words = set(_words(request))
        self.numbers = _read_numbers(self.text)
        self.has_date = bool(DATE_HINT_RE.search(self.text))
        # dates written in full: a date the AI gives must then be one of them, unless the request also
        # says a date in words ("tomorrow"), that the AI computes
        self.iso_dates = set(re.findall(r'\b\d{4}-\d{2}-\d{2}\b', self.text))
        self.has_other_date = bool(DATE_HINT_RE.search(re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', self.text)))

    def mentions(self, text):
        """ Whether the request says a text: its words, or the text itself when it has
        no word worth checking (a code). """
        text = str(text).strip().lower()
        words = [word for word in _words(text) if len(word) > 2 and word not in STOPWORDS]
        if not words:
            return bool(text) and text in self.text
        return all(_mentions(self.words, word) for word in words)

    def quotes(self, words, field=None, value=None):
        """ Whether the words the AI quotes for a value are a few words of the request
        saying it: a number quoted in figures must be the one the AI gives. """
        words = re.sub(r'\s+', ' ', str(words or '')).strip().lower()
        if not words or len(words.split()) > MAX_QUOTED_WORDS or words not in re.sub(r'\s+', ' ', self.text):
            return False
        if not re.search(r'\d', words):
            # in words ("two", "tomorrow"): words the agent also read as a number or a date, else at least a
            # word saying something ("then" or "the" say no date)
            return any(words in spoken or spoken in words for spoken in self.spoken) or any(
                len(word) > 2 and word not in STOPWORDS for word in _words(words))
        if field is not None and field.type in ('integer', 'float', 'monetary'):
            try:
                return float(value) in _read_numbers(words)
            except (TypeError, ValueError):
                return False
        return True

    def supports(self, field, value, quoted=None):
        """ Whether the request gives a value: as it is written, or, for a number, a date
        or a choice written in words ("two", "tomorrow"), by the words the AI quotes, that
        the agent read as a number or a date too. """
        if field.type in QUOTED_TYPES and not isinstance(value, dict) and self.quotes(quoted, field, value):
            if field.type == 'selection':
                # the words quoted must say the choice ("urgent"), not only exist ("a new product" for combo)
                labels = [label for key, label in field._description_selection(self.env) if str(key) == str(value)]
                return any(self.mentions(label) or any(
                    _similar(_stem(word), _stem(other)) for word in _words(quoted) for other in _words(label)
                    if len(word) > 2) for label in labels)
            if field.type == 'boolean':
                return self.mentions(field._description_string(self.env))
            return True
        if isinstance(value, dict):
            # records described or created by the request: their description is its own words, and
            # more than the label of the field ("Sales Taxes"), which an AI may give for a value
            text = _get_query(value) or _get_new(value)
            label = _keywords(field._description_string(self.env))
            return bool(text) and self.mentions(text) and not _keywords(text) <= label
        if field.type in ('integer', 'float', 'monetary'):
            try:
                return float(value) in self.numbers
            except (TypeError, ValueError):
                return False
        if field.type in ('date', 'datetime'):
            if self.iso_dates and not self.has_other_date:
                return str(value).strip()[:10] in self.iso_dates
            return self.has_date
        if field.type == 'boolean':
            return self.mentions(field._description_string(self.env))
        if field.type == 'selection':
            labels = [label for key, label in field._description_selection(self.env) if str(key) == str(value)]
            return any(self.mentions(label) for label in labels)
        if field.type == 'many2many':
            names = value if isinstance(value, list) else [value]
            return any(self.supports(field, name) if isinstance(name, dict) else self.mentions(name) for name in names)
        return self.mentions(value)


def _plain(text):
    """ A name without case, spaces or punctuation, to compare names written otherwise. """
    return re.sub(r'[^0-9a-z]+', '', str(text or '').lower())


def _get_new(value):
    """ The name of a linked record an AI gave as not existing yet, if any:
    ``{"$new": "John Doe"}``. """
    if isinstance(value, dict) and isinstance(name := value.get('$new'), str) and name.strip():
        return name
    return None


def _resolve_steps(value, steps, env=None):
    """ A value of a step of a plan, with the references to the records created by the
    previous steps (``{"$step": index}``) replaced by their id. A reference to a record
    of another model stored with it (``"$as"``: the variant of a product template
    created) is replaced by the id of that record. """
    if isinstance(value, dict):
        if set(value) - {'$as'} == {'$step'}:
            step = steps[value['$step']]
            res_id = step.get('res_id') or False
            target = value.get('$as')
            if res_id and env is not None and target and target != step['model'] and target in env:
                Target = env[target]
                if link := Target._inherits.get(step['model']):
                    return Target.search([(link, '=', res_id)], limit=1).id or False
                if link := env[step['model']]._inherits.get(target):
                    return env[step['model']].browse(res_id)[link].id or False
            return res_id
        return {key: _resolve_steps(item, steps, env) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_resolve_steps(item, steps, env) for item in value]
    return value


def _replace_placeholder(step, placeholder, name):
    """ Show the name of a record created by a step of a plan, instead of the name it
    was drafted with, in the values of a next step. """
    if not placeholder:
        return
    for field in step['fields']:
        field['value'] = str(field['value']).replace(placeholder, name)
    for table in step['lines']:
        table['rows'] = [[str(cell).replace(placeholder, name) for cell in row] for row in table['rows']]


def _get_query(value):
    """ The description of records an AI gave instead of their name, if any:
    ``{"$query": "my top 5 selling products"}``. """
    if isinstance(value, dict) and isinstance(query := value.get('$query'), str) and query.strip():
        return query
    return None


def _get_query_count(value):
    """ The number of records the AI read in the request for a description of records:
    ``{"$query": "most selling products", "$count": 5}``, else ``False``. """
    count = value.get('$count') if isinstance(value, dict) else None
    try:
        count = int(count)
    except (TypeError, ValueError):
        return False
    return min(count, MAX_LIMIT) if count > 0 else False


def _loads_loosely(text):
    """ The JSON object of a text written by an AI, which may surround it with words
    or a code block, and mismatch its brackets ("[{...}}]"): closing brackets that
    match no opening one are dropped, and those missing are added. ``None`` when no
    object can be read. """
    start = (text or '').find('{')
    if start < 0:
        return None
    text = text[start:]
    try:
        return json.loads(text[:text.rfind('}') + 1])
    except json.JSONDecodeError:
        pass
    repaired, stack, in_string, escaped = [], [], False, False
    for char in text:
        if repaired and not stack and not in_string:
            # the object is closed: what follows is text
            break
        if in_string:
            repaired.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in CLOSING:
            stack.append(CLOSING[char])
        elif char in '}]':
            if not stack or stack[-1] != char:
                continue
            stack.pop()
        repaired.append(char)
    repaired += reversed(stack)
    try:
        return json.loads(''.join(repaired))
    except json.JSONDecodeError:
        return None


class AiChatAssistant(models.AbstractModel):
    """ Records created from the chat ("create a sales order for Azure Interior with 3
    chairs", "new contact John Smith, john@example.com").

    The kind of record is detected like the data of a question, among the models the
    user can create. Odoo's AI service (OLG) then reads the values of the request,
    given only the fields of the form of that model, never any record. These values are
    checked and turned into a draft by Odoo, as the user asking: related records are
    found by their name, among those the user can read. The draft is only created when
    the user confirms it, with the access rights of the user.
    """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _is_create_enabled(self):
        return str2bool(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.allow_create') or 'False', False)

    # ------------------------------------------------------------
    # Model to create
    # ------------------------------------------------------------

    @api.model
    def _is_line_model(self, Model):
        """ Whether the records of a model are lines of another record (order lines,
        invoice lines): they link to it by a required field, and go with it. """
        if any(entry[3] for entry in self._get_model_catalog() if entry[0] == Model._name):
            # reached by a menu of its own (product variants): a record of its own
            return False
        return any(field.type == 'many2one' and field.required and field.ondelete == 'cascade'
                   and not field.related for field in Model._fields.values())

    @api.model
    def _is_numbered(self, Model):
        """ Whether Odoo names the records of a model itself, by a sequence: their name
        has a default ("New", replaced by S00042 when created). """
        rec_name = Model._rec_name
        if not rec_name or rec_name not in Model._fields or Model._fields[rec_name].type != 'char':
            return False
        try:
            return bool(Model.default_get([rec_name]).get(rec_name))
        except (AccessError, UserError):
            return False

    @api.model
    def _is_settings_model(self, model_name):
        """ Whether the records of a model are reached only from the Settings app (users,
        companies of the database). """
        paths = [menu[0] for entry in self._get_model_catalog() if entry[0] == model_name for menu in entry[3]]
        return bool(paths) and all(self._is_settings_candidate({'path': path}) for path in paths)

    @api.model
    def _is_settings_candidate(self, candidate):
        """ Whether a kind of record is reached from the Settings app: it configures the
        software, rather than holding business data. """
        settings = self.env.ref('base.menu_administration', raise_if_not_found=False)
        path = candidate.get('path') or ''
        return bool(settings and path) and path.split('/')[0] == settings.name

    @api.model
    def _can_create(self, model_name):
        if not self._is_allowed_model(model_name):
            return False
        Model = self.env[model_name]
        # reports are SQL views: they can not be created
        return Model._auto and Model.has_access('create')

    @api.model
    def _choose_create_model(self, question, head, usage, whole=None):
        """ The kind of record a request asks to create, and the menu it is created from
        (see ``_choose_create_kind`` and ``_pick_create_menu``). """
        candidate = self._choose_create_kind(question, head, usage, whole=whole)
        return candidate and self._pick_create_menu(question, candidate, usage)

    @api.model
    def _pick_create_menu(self, question, candidate, usage):
        """ The menu a record is created from, when the words of the request named its
        kind but no menu: the only one with defaults, else the one the decision model
        chooses (Invoices or Bills, for a journal entry). """
        if candidate.get('path'):
            return candidate
        catalog = {entry[0]: entry[3] for entry in self._get_model_catalog()}
        configuration = self._get_configuration_paths()
        options, seen = [], set()
        for path, domain, context, search_view_id, _menu_words in catalog.get(candidate["model"]) or ():
            option = dict(candidate, path=path, domain=domain, context=context, search_view_id=search_view_id)
            defaults = json.dumps(self._get_import_context(option), sort_keys=True, default=str)
            if path in configuration or self._is_settings_candidate(option) or defaults in seen:
                continue
            seen.add(defaults)
            options.append(option)
        if not options:
            return candidate
        if len(options) == 1:
            return options[0]
        criteria = {
            f"option_{index}": f"{option['path']}" + (f" (creating with {defaults})" if (defaults := ", ".join(
                f"{key.removeprefix('default_')}={value}" for key, value in self._get_import_context(option).items()))
                else '')
            for index, option in enumerate(options)
        }
        answers = self._decide(question, {'menu': {
            'type': 'choice',
            'instructions': f"From which menu is the {candidate['label']} of the request created?",
            'criteria': criteria,
        }}, usage)
        return options[int(self._get_choice(answers, 'menu', criteria, 'option_0').removeprefix('option_'))]

    @api.model
    def _choose_create_kind(self, question, head, usage, whole=None):
        """ The kind of record a request asks to create (as the agent read it, see
        ai_chat_agent), among the models the user can create, matched on the words
        naming it (``head``); ``None`` when the user can create none of them. The
        decision model chooses when several match as well.

        :param str whole: the whole request, when ``question`` is a part of a request
            creating several records
        """
        candidates = [c for c in self._find_candidates(_keywords(head)) if self._can_create(c['model'])]
        # the kinds of records users create from a menu of their apps, before technical ones and the settings
        if usual := [c for c in candidates if c.get('menu_names') and not self._is_settings_candidate(c)]:
            candidates = usual
        if not candidates:
            return None
        best, second = candidates[0], candidates[1] if len(candidates) > 1 else None
        is_clear = not second or best['score'] >= CLEAR_WINNER_RATIO * second['score']
        # the only kind of record all the words name ("vendor bill": the Bills of the Vendors, not the Bills
        # of Materials) is the one meant
        keywords = _keywords(head)

        def own_words(c):
            return _keywords(c['label']) | {word for name in c.get('menu_names') or [] for word in _keywords(name)}

        # the kinds whose own name (their label, the names of their menus: not the name of their app) says every
        # word of the request: "vendor bill" names the Bills of the vendors, not the Bills of Materials
        whole_matches = [c for c in candidates if not self._is_settings_candidate(c)
                         and all(any(_similar(keyword, word) for word in own_words(c)) for keyword in keywords)]
        if len(whole_matches) == 1:
            return whole_matches[0]
        if len(whole_matches) > 1:
            # the kind named exactly ("contact": Contact, not Contact Tags; "invoice": Invoices), else the main
            # data of the apps (the one reached by the most menus: sales orders, not quotation templates)
            exact = [c for c in whole_matches if _keywords(c['label']) == keywords
                     or any(_keywords(name) == keywords for name in c.get('menu_names') or [])]
            if len(exact) == 1:
                return exact[0]
            ranked = sorted(exact or whole_matches, key=lambda c: -(c.get('menu_count') or 0))
            if ranked[0].get('menu_count', 0) > (ranked[1].get('menu_count', 0) if len(ranked) > 1 else 0):
                return ranked[0]
        if is_clear and not self._is_settings_candidate(best):
            return best
        options = [best] if is_clear else [c for c in candidates if c['score'] * CLEAR_WINNER_RATIO > best['score']]
        if self._is_settings_candidate(best):
            # a record configuring the software (a company of the database, a user) is rarely what a chat
            # creates: the decision model chooses it or another kind of record the request names (a contact)
            others = [c for c in self._find_candidates(_keywords(whole or question))
                      if self._can_create(c['model']) and c.get('menu_names') and not self._is_settings_candidate(c)
                      and c['model'] not in {option['model'] for option in options}]
            options += others[:3]
        if len(options) == 1:
            return options[0]
        criteria = {
            f"option_{index}": f"{c['label']} [{c['model']}]" + (f" (menu {c['path']})" if c.get('path') else '')
            + (f", known as: {', '.join(c['menu_names'])}" if c.get('menu_names') else '')
            for index, c in enumerate(options)
        }
        state = f"{whole}\n(Part of the request considered: {question})" if whole and whole != question else question
        answers = self._decide(state, {'record': {
            'type': 'choice',
            'instructions': "Which kind of record must be created? A customer, vendor, person or company the business "
                            "deals with is a contact; the records of the Settings menus configure the software itself.",
            'criteria': criteria,
        }}, usage)
        return options[int(self._get_choice(answers, 'record', criteria, 'option_0').removeprefix('option_'))]

    # ------------------------------------------------------------
    # Fields to fill
    # ------------------------------------------------------------

    @api.model
    def _get_create_form_view(self, candidate):
        """ The form view of the menu a record to create was matched on, if it has one:
        the default form of a model may be another app's (timesheets: the form of
        analytic items, with an amount instead of the hours spent). """
        if not candidate.get('path'):
            return False
        Menu = self.env['ir.ui.menu']
        for menu in Menu.sudo().browse(Menu._visible_menu_ids(debug=False)):
            action = menu.action
            if (menu.complete_name or menu.name) != candidate['path'] or action._name != 'ir.actions.act_window' \
                    or action.res_model != candidate['model']:
                continue
            view = next((line.view_id for line in action.view_ids if line.view_mode == 'form' and line.view_id),
                        action.view_id if action.view_id.type == 'form' else None)
            return view.id if view else False
        return False

    @api.model
    def _get_create_fields(self, Model, linked_models=(), form_view_id=False):
        """ The fields of a model a request can fill: those linking to the records the
        request creates before (``linked_models``), those of its form the user can
        write, then its required fields. One2many fields hold the fields of their lines,
        from the views of the lines in the form.

        :return: ``{field name: {sub field name: None}}`` for lines, else ``None``
        """
        arch = etree.fromstring(Model.get_views([(form_view_id or False, 'form')])['views']['form']['arch'])
        # the default form may not show them (timesheets: the form of analytic items, without their task)
        names = [
            name for name, field in Model._fields.items()
            if field.type in ('many2one', 'many2many') and field.comodel_name in linked_models
            and self._is_creatable_field(Model, field)
        ]
        line_names = {}
        for node in arch.iter('field'):
            name = node.get('name')
            if any(parent.tag == 'field' for parent in node.iterancestors()) or node.get('invisible') in ('1', 'True'):
                continue
            field = Model._fields.get(name)
            if not field or not self._is_creatable_field(Model, field):
                continue
            if field.type == 'one2many' and any(
                    Model._fields[other].comodel_name == field.comodel_name for other in line_names):
                # the lines of the form once: the invoice lines, not the journal items of the same invoice
                continue
            names.append(name)
            if field.type == 'one2many':
                Line = self.env[field.comodel_name]
                # the columns users see in the lines: hidden ones are technical
                line_names[name] = [
                    sub.get('name') for sub in node.iter('field')
                    if sub is not node and sub.get('name') != field.inverse_name
                    and sub.get('column_invisible') not in ('1', 'True') and sub.get('invisible') not in ('1', 'True')
                    and (sub_field := Line._fields.get(sub.get('name')))
                    and sub_field.type != 'one2many' and self._is_creatable_field(Line, sub_field)
                ]
        names += [
            name for name, field in Model._fields.items()
            if field.required and not field.compute and not field.related and self._is_creatable_field(Model, field)
        ]
        create_fields = {}
        for name in dict.fromkeys(names):
            if Model._fields[name].type == 'one2many' and name not in line_names:
                # lines the form does not show, Odoo fills them itself (the variants of a product)
                continue
            if name in line_names:
                sub_names = list(dict.fromkeys(line_names[name]))[:MAX_LINE_FIELDS]
                if not sub_names or sum(1 for value in create_fields.values() if value) >= MAX_LINE_FIELDS_PER_RECORD:
                    continue
                create_fields[name] = dict.fromkeys(sub_names)
            else:
                create_fields[name] = None
        return dict(list(create_fields.items())[:MAX_CREATE_FIELDS])

    @api.model
    def _is_creatable_field(self, Model, field):
        """ Whether the current user can set a field when creating a record. """
        if (
            field.name in SKIPPED_FIELD_NAMES or field.name in SKIPPED_CREATE_FIELDS
            or field.name in Model._inherits.values()
            or field.name.startswith(SKIPPED_FIELD_PREFIXES) or field.type in SKIPPED_FIELD_TYPES
            or field.readonly or not (field.store or field.inverse) or not Model._has_field_access(field, 'write')
        ):
            return False
        if field.relational:
            if field.comodel_name.startswith(EXCLUDED_MODEL_PREFIXES):
                return False
            if field.compute and self._is_configuration_model(field.comodel_name):
                # the account of a line, its taxes, the operation type of an order: computed by Odoo from
                # the other values, set up in the configuration, never asked from a request
                return False
            Comodel = self.env[field.comodel_name]
            if field.type == 'one2many':
                return Comodel.has_access('create')
            return Comodel.has_access('read')
        return True

    @api.model
    def _describe_create_field(self, Model, field, sub_fields=None):
        """ A field as the AI is told about it: its name, label and the JSON value it
        takes. """
        label = field._description_string(self.env)
        kind = {
            'char': "text",
            'text': "text",
            'integer': "integer",
            'float': "number",
            'monetary': "amount, a number",
            'boolean': "true or false",
            'date': "date \"YYYY-MM-DD\"",
            'datetime': "date and time \"YYYY-MM-DD HH:MM\"",
        }.get(field.type)
        if field.type == 'selection':
            selection = field._description_selection(self.env)[:MAX_SELECTION_OPTIONS]
            kind = "one of the keys: " + ", ".join(f"{key} ({value})" for key, value in selection)
        elif field.type == 'many2one':
            kind = f"name of an existing {self.env[field.comodel_name]._description}, or {{\"$query\": ...}}"
        elif field.type == 'many2many':
            kind = (f"list of names of existing {self.env[field.comodel_name]._description} records, "
                    "or {\"$query\": ...}")
        elif field.type == 'one2many':
            Line = self.env[field.comodel_name]
            kind = "list of lines, objects with: " + "; ".join(
                self._describe_create_field(Line, Line._fields[name]) for name in sub_fields
            )
        required = ", required" if field.required else ""
        return f"{field.name} ({label}, {kind}{required})"

    # ------------------------------------------------------------
    # Draft
    # ------------------------------------------------------------

    @api.model
    def _draft_record(self, question, candidate, usage):
        """ The draft of the record a request asks to create, shown to the user to
        confirm. When it links to records that do not exist yet (a new customer, a new
        product), these are drafted too, as the first steps of a plan: the user creates
        them one after the other, and each one is linked to the next steps. """
        steps = []
        main = self._build_draft(question, candidate['model'], candidate['label'], usage, steps=steps,
                                 form_view_id=self._get_create_form_view(candidate),
                                 kind_names=tuple(candidate.get('menu_names') or ()))
        # the defaults of the menu the record is created from: Bills create vendor bills, not entries
        main['context'] = self._get_import_context(candidate)
        main['missing'] = self._get_missing_fields(self.env[candidate['model']].with_context(**main['context']),
                                                   main['values'])
        if not steps:
            result = main
            values = main['values']
            if values:
                content = self.env._("Here is the %(label)s to create. Check it, then create it.",
                                     label=main['model_label'])
        else:
            steps.append(main)
            result = {
                'type': 'plan',
                'state': 'draft',
                'current': 0,
                'title': main['title'],
                'model_label': main['model_label'],
                'steps': steps,
            }
            values = True
            content = self.env._(
                "Creating this %(label)s takes %(count)s steps, as it needs records that do not exist yet. Check "
                "and create them one after the other.", label=main['model_label'], count=len(steps),
            )
        if not values:
            content = self.env._(
                "I understood you want to create a %(label)s, but found no value for it in your request. "
                "Open the form to fill it in, or describe it again.", label=main['model_label'],
            )
        # the values are read by Odoo's AI service, the record to create by the decision model
        source = 'openrouter_olg' if usage['ai_called'] else 'olg'
        return {'content': content, 'result': result, 'source': source}

    @api.model
    def _share_sibling_links(self, steps, main_indexes):
        """ Records of one kind named in one breath ("contacts Ann and Ben at the new company
        X"): a link one of them got and the others lack is theirs too. """
        by_model = {}
        for index in main_indexes:
            by_model.setdefault(steps[index]['model'], []).append(index)
        for model_name, indexes in by_model.items():
            if len(indexes) < 2:
                continue
            Model = self.env[model_name]
            for name, field in Model._fields.items():
                if field.type != 'many2one':
                    continue
                values = {json.dumps(steps[index]['values'].get(name), sort_keys=True)
                          for index in indexes if steps[index]['values'].get(name)}
                if len(values) == 1:
                    value = json.loads(values.pop())
                    for index in indexes:
                        if not steps[index]['values'].get(name):
                            steps[index]['values'][name] = value
        return steps

    @api.model
    def _draft_records(self, requests, usage, siblings=False):
        """ The plan creating the records of a request asking for several ones, one
        step per part of the request, in its order. The values of each record are read
        from its part only, and may link to the records of the parts before it ("a task
        in that project"), created first. """
        steps, main_steps = [], []
        for request in requests:
            text, candidate = request[:2]
            # the parts this part refers to ("in that project"), as the agent read them; else those it names
            refers = request[2] if len(request) > 2 else None
            if refers is None:
                linkable = {index for index in main_steps
                            if steps[index].get('new_name') and steps[index]['new_name'].lower() in text.lower()}
            else:
                linkable = {main_steps[index] for index in refers if 0 <= index < len(main_steps)}
            Model = self.env[candidate['model']]
            step = self._build_draft(text, candidate['model'], candidate['label'], usage, steps=steps, follows=True,
                                     form_view_id=self._get_create_form_view(candidate), linkable=linkable,
                                     kind_names=tuple(candidate.get('menu_names') or ()))
            # the defaults of the menu the record is created from: Invoices create invoices, not entries
            step['context'] = self._get_import_context(candidate)
            step['missing'] = self._get_missing_fields(Model.with_context(**step['context']), step['values'])
            # the name the next parts link to it by (a category is named by its complete name, computed)
            name = step['values'].get(Model._rec_name) or step['values'].get('name')
            name = name.strip() if isinstance(name, str) else ''
            # the next parts link to it by its name
            step.update(new_name=name, placeholder=self.env._("%s (new)", name) if name else '')
            if name:
                step['title'] = self.env._("New %(label)s: %(name)s", label=candidate['label'], name=name)
            main_steps.append(len(steps))
            steps.append(step)
        if siblings:
            steps = self._share_sibling_links(steps, main_steps)
        steps = self._merge_plan_steps(steps, main_steps)
        labels = ", ".join(dict.fromkeys(step['model_label'] for step in steps))
        result = {
            'type': 'plan',
            'state': 'draft',
            'current': 0,
            'title': self.env._("New %s", labels),
            'model_label': labels,
            'steps': steps,
            # each step is a record asked for, not a record another one needs
            'several': True,
        }
        content = self.env._(
            "Your request creates %(count)s records: %(labels)s. Check and create them one after the other.",
            count=len(steps), labels=labels,
        )
        source = 'openrouter_olg' if usage['ai_called'] else 'olg'
        return {'content': content, 'result': result, 'source': source}

    @api.model
    def _link_referred_steps(self, Model, raw_values, earlier, steps):
        """ The values of a record, linked to the records of the earlier parts it refers
        to, when nothing links to them yet and exactly one field of the record can. """
        def linked(step):
            name = step['new_name'].strip().lower()
            for field_name, value in raw_values.items():
                field = Model._fields.get(field_name)
                if field and field.relational and name in (str(value).strip().lower(),
                                                           str(_get_new(value) or '').strip().lower()):
                    return True
            return False

        form_order = list(self._get_create_fields(Model))

        def linking_fields(model_name):
            family = self._get_model_family(model_name)
            fields_ = [field for field in Model._fields.values()
                       if field.type == 'many2one' and field.comodel_name in family
                       and self._is_creatable_field(Model, field) and not raw_values.get(field.name)]
            # the first field of the form (the customer of an invoice, before its delivery address)
            return sorted(fields_, key=lambda field: form_order.index(field.name) if field.name in form_order else 99)

        for step in earlier:
            if not step.get('new_name') or linked(step):
                continue
            if fields_ := linking_fields(step['model']):
                # the name of the record in a text field is the link, misplaced ("Zeta Parts" as a bill's reference)
                raw_values = {name: value for name, value in raw_values.items()
                              if not (Model._fields[name].type == 'char' and name != Model._rec_name
                                      and str(value).strip().lower() == step['new_name'].strip().lower())}
                raw_values = {**raw_values, fields_[0].name: step['new_name']}
                continue
            # no field links to the record referred to (an invoice "for him", him being the customer of the order
            # before): the records that record links to, when the record can link to them too
            for value in (step.get('values') or {}).values():
                index = value.get('$step') if isinstance(value, dict) and set(value) - {'$as'} == {'$step'} else None
                if index is not None and index < len(steps) and steps[index].get('new_name') \
                        and not linked(steps[index]) and (fields_ := linking_fields(steps[index]['model'])):
                    raw_values = {**raw_values, fields_[0].name: steps[index]['new_name']}
        return raw_values

    @api.model
    def _merge_plan_steps(self, steps, main_indexes):
        """ The steps of a plan creating several records, each record once: a record a
        part needed and drafted before another part creates it (the new company of two
        contacts) is the one of that part. The steps are then ordered so that each record
        is created before the ones linking to it. """
        target = {}
        for index, step in enumerate(steps):
            if not step.get('new_name'):
                continue
            # the step of a part before it, else of any part, creating a record of the same name
            twin = next((other for other in main_indexes if other != index and other not in target
                         and (other < index or index not in main_indexes) and steps[other]['model'] == step['model']
                         and _plain(steps[other].get('new_name')) == _plain(step['new_name'])), None)
            if twin is not None:
                target[index] = twin

        def remap(value):
            if isinstance(value, dict):
                if set(value) - {'$as'} == {'$step'}:
                    return {**value, '$step': target.get(value['$step'], value['$step'])}
                return {key: remap(item) for key, item in value.items()}
            if isinstance(value, list):
                return [remap(item) for item in value]
            return value

        def references(value):
            if isinstance(value, dict):
                if set(value) - {'$as'} == {'$step'}:
                    return {value['$step']}
                return set().union(*(references(item) for item in value.values())) if value else set()
            if isinstance(value, list):
                return set().union(*(references(item) for item in value)) if value else set()
            return set()

        kept = [index for index in range(len(steps)) if index not in target]
        for index in kept:
            steps[index]['values'] = remap(steps[index]['values'])
        # each record after the ones it links to
        ordered = []
        while kept:
            index = next((index for index in kept if references(steps[index]['values']) <= set(ordered)), kept[0])
            ordered.append(index)
            kept.remove(index)
        position = {old: new for new, old in enumerate(ordered)}

        def renumber(value):
            if isinstance(value, dict):
                if set(value) - {'$as'} == {'$step'}:
                    return {**value, '$step': position.get(value['$step'], value['$step'])}
                return {key: renumber(item) for key, item in value.items()}
            if isinstance(value, list):
                return [renumber(item) for item in value]
            return value
        return [{**steps[index], 'values': renumber(steps[index]['values'])} for index in ordered]

    @api.model
    def _build_draft(self, question, model_name, label, usage, steps=None, new_name=None, follows=False,
                     form_view_id=False, linkable=None, warn_dropped=True, kind_names=()):
        """ The draft of a record, from the values a request gives it.

        :param list steps: the drafts of the records to create first, which the draft
            may add to; ``None`` when records not found are not to be created
        :param str new_name: the name the request gives to a linked record to create
        :param bool follows: whether ``question`` is a part of a request creating
            several records, that may link to the records of ``steps``
        :param int form_view_id: the form whose fields the request fills, else the
            default form of the model
        :param set linkable: with ``follows``, the indexes of the steps the part refers
            to, the only ones it may link to; ``None`` for all
        :param bool warn_dropped: whether the values the request may not give are said:
            not for the changes of a copy, that keeps the values of the record copied
        :param tuple kind_names: what users call these records (the names of their menus:
            "Customers"), besides ``label``
        """
        Model = self.env[model_name]
        earlier = [
            step for index, step in enumerate(steps or [])
            if step.get('new_name') and (linkable is None or index in linkable)
        ] if follows else []
        create_fields = self._get_create_fields(Model, linked_models={step['model'] for step in earlier},
                                                form_view_id=form_view_id)
        if new_name:
            # a record created for another one is created with its own values only: lines would be
            # parts of the request meant for the other record (the products of an order for a new customer)
            create_fields = {name: sub_fields for name, sub_fields in create_fields.items() if not sub_fields}
        request = question
        if new_name:
            question = (f"{request}\n(Only the {Model._description} \"{new_name}\" is to be created now: give the "
                        "values the request gives to it.)")
        # the names of the records of the parts before, that the part refers to ("that project")
        grounding = request
        if earlier:
            names = "; ".join(f"{self.env[step['model']]._description} \"{step['new_name']}\"" for step in earlier)
            question = (f"{question}\n(Created just before, by the same request: {names}. To link to one of them, "
                        "give its name exactly as written here.)")
            grounding = f"{request}\n{names}"
        raw_values = self._extract_values(question, Model, create_fields, usage) if create_fields else {}
        read = raw_values
        raw_values = self._keep_grounded_values(grounding, Model, create_fields, raw_values)
        # the values the request writes (as the AI quotes them) that could not be checked: left to the user,
        # and said, rather than set (values the request does not write at all are made up, and dropped silently)
        quoted = read.get('$from') if isinstance(read.get('$from'), dict) else {}
        dropped = [Model._fields[name]._description_string(self.env) for name in read
                   if name in Model._fields and name not in raw_values
                   and (words := str(quoted.get(name) or '').strip().lower()) and words in grounding.lower()]
        if new_name:
            # records described by the request are for the record it asks for, not for this one
            raw_values = {name: value for name, value in raw_values.items() if not _get_query(value)}
        rec_name = Model._rec_name
        if rec_name in create_fields and Model._fields[rec_name].type == 'char' and not raw_values.get(rec_name) \
                and not new_name:
            # the AI gave no name: the one the agent read as the new record of this kind ("a customer Zeta One"),
            # the one the part says when the request is cut in parts ("...to create now: Ann Zeta")
            hint = question.rsplit('\n', 1)[-1] if '\n' in question else ''
            kinds = [label, self._get_intent().get('target') or '', *kind_names]
            named = [name['text'] for name in self._get_intent().get('names') or []
                     if name.get('new') and any(self._same_kind(name.get('label') or '', kind) for kind in kinds)
                     and name['text'].lower() in (hint or question).lower()]
            if len(named) == 1:
                raw_values[rec_name] = named[0]
        if self._is_numbered(Model):
            # a name Odoo numbers itself (S00042): never one the request gives, that names another record
            raw_values.pop(rec_name, None)
        if new_name and rec_name in create_fields and Model._fields[rec_name].type == 'char':
            raw_values[rec_name] = new_name
        # the name of the record is not the name of a record it links to, nor another value of it: "a project
        # called Cybrosys" is not for a customer Cybrosys, "a contact Acme Ltd" is not of a company Acme Ltd
        own_name = raw_values.get(rec_name)
        if isinstance(own_name, str) and own_name.strip():
            own_name = own_name.strip().lower()
            raw_values = {
                name: value for name, value in raw_values.items()
                if name == rec_name or not (Model._fields[name].type in ('many2one', 'many2many', 'char')
                                            and str(_get_new(value) or value).strip().lower() == own_name)
            }
        # what to check before creating, and how records described by the request were found
        warnings, notes = [], []
        if earlier:
            # the records of the parts this part refers to ("a product in it"): linked by the only field that can,
            # when the values read say nothing of them
            raw_values = self._link_referred_steps(Model, raw_values, earlier, steps)
        if dropped and warn_dropped:
            warnings.append(self.env._("Not set, as the request may not give it: %s. Fill it in the form if needed.",
                                       ", ".join(dropped)))
        report = {
            'warnings': warnings, 'notes': notes, 'usage': usage, 'request': request, 'steps': steps,
        }
        values, shown, lines = {}, [], []
        for name, sub_fields in create_fields.items():
            raw = raw_values.get(name)
            if raw in (None, '', [], {}):
                continue
            field = Model._fields[name]
            if field.type == 'one2many':
                commands, table = self._resolve_lines(field, sub_fields, raw, report)
                if commands:
                    values[name] = commands
                    lines.append(table)
                continue
            resolved = self._resolve_value_for_create(Model, field, raw, report)
            if resolved is not None:
                values[name], display = resolved
                shown.append({'label': field._description_string(self.env), 'value': display})
        return {
            'type': 'draft',
            'state': 'draft',
            'model': model_name,
            'model_label': label,
            'title': self.env._("New %(label)s: %(name)s", label=label, name=new_name) if new_name
            else self.env._("New %s", label),
            'fields': shown,
            'lines': lines,
            'warnings': warnings,
            'notes': notes,
            'missing': self._get_missing_fields(Model, values),
            'values': values,
            # the records the user is to choose among, several matching a name of the request
            'choices': report.get('choices') or [],
        }

    @api.model
    def _extract_values(self, question, Model, create_fields, usage=None):
        """ The values a request gives to the fields of a record to create, read by
        Odoo's AI service (OLG), that is only given the fields, never any record. """
        described = "\n".join(
            f"- {self._describe_create_field(Model, Model._fields[name], sub_fields)}"
            for name, sub_fields in create_fields.items()
        )
        tz = self.env.user.tz or 'UTC'
        now = datetime.now(pytz.timezone(tz))
        prompt = (
            "You fill in a new record of the Odoo business software from the request of a user. Return the "
            "values the request gives, explicitly or clearly implied, and nothing else: never invent a value, "
            "never fill a field with a default or a guess. Use only the field names listed below, matching what "
            "the request says with the label of each field (\"works at X\" is the company of a contact, \"for X\" "
            "the customer of an order). For links to "
            "other records, give the name exactly as the user wrote it. When the request describes records "
            "instead of naming them (\"my top 5 selling products\", \"products of the Desks category\", \"our "
            "biggest customer\"), never make up names: give {\"$query\": \"<the description>\", \"$count\": <the "
            "number of these records the request asks for, wherever it says it, or null>} instead (\"5 of the least "
            "sold products\", \"our most selling 5 products\" and \"the least sold products. Five products\" are "
            "{\"$query\": \"least sold products\", \"$count\": 5}). For lines, give a single line with that object in its link field and the values that apply "
            "to each record: it becomes one line per record found. Give every value the request states for a "
            "line: its quantity, its unit price (\"at 120 each\"), its discount, its description. When the request "
            "says a linked record does "
            "not exist yet (\"a new customer John Doe\", \"a new product Desk X\"), give {\"$new\": \"<its name>\"}. "
            "Write numbers as numbers (\"two\" is 2). For each value, give in \"from\" the words of the request it is "
            "read from, copied exactly (for lines, in a \"$from\" object of the line). "
            f"Today is {now.strftime('%A %Y-%m-%d')}, the user's time zone is {tz}: dates are YYYY-MM-DD and "
            "date-times YYYY-MM-DD HH:MM in that time zone.\n"
            "Reply with ONLY minified JSON, no text and no code block. Examples:\n"
            '{"values":{"partner_id":"Azure Interior","order_line":[{"product_id":"Office Chair",'
            '"product_uom_qty":3,"$from":{"product_uom_qty":"three"}}],"tag_ids":["VIP"],'
            '"date_order":"2026-05-02"},"from":{"partner_id":"Azure Interior","date_order":"tomorrow"}}\n'
            '{"values":{"partner_id":"Gemini Furniture","order_line":[{"product_id":{"$query":"top selling '
            'products","$count":5},"product_uom_qty":2}]}}\n'
            f"Record: {Model._description} [{Model._name}]\nFields:\n{described}\n"
            f"Request: {question}"
        )
        content = self._complete_values(prompt, usage)
        answer = _loads_loosely(content)
        if answer is None:
            _logger.info("AI Chat Pro: values of a record to create are no JSON: %s", (content or '')[:500])
        values = answer.get('values') if isinstance(answer, dict) else None
        if not isinstance(values, dict):
            return {}
        quoted = answer.get('from') if isinstance(answer.get('from'), dict) else {}
        values = {name: value for name, value in values.items() if name in create_fields}
        # the words each value is read from, kept with the values to check them
        if quoted := {name: words for name, words in quoted.items() if name in values}:
            values['$from'] = quoted
        return values

    @api.model
    def _keep_grounded_values(self, request, Model, create_fields, raw_values):
        """ The values read by the AI that the request gives: a value the request does
        not mention (a unit, taxes, a category, today's date filled in as a default) is
        made up, and left to the defaults of Odoo. """
        grounding = _Grounding(self.env, request, self._get_intent().get('spoken') or ())
        quoted = raw_values.get('$from') if isinstance(raw_values.get('$from'), dict) else {}
        kept = {}
        for name, raw in raw_values.items():
            if name == '$from':
                continue
            field = Model._fields[name]
            if field.type == 'one2many':
                Line = self.env[field.comodel_name]
                lines = []
                for line in (raw if isinstance(raw, list) else []):
                    if not isinstance(line, dict):
                        continue
                    line_quoted = line.get('$from') if isinstance(line.get('$from'), dict) else {}
                    lines.append({
                        sub: value for sub, value in line.items()
                        if sub in create_fields[name]
                        and grounding.supports(Line._fields[sub], value, line_quoted.get(sub))
                    })
                kept[name] = [line for line in lines if line]
            elif grounding.supports(field, raw, quoted.get(name)):
                kept[name] = raw
            else:
                _logger.info("AI Chat Pro: value of %s.%s not in the request, ignored: %r", Model._name, name, raw)
        return kept

    @api.model
    def _complete_values(self, prompt, usage=None):
        """ The answer of Odoo's AI service (OLG) to the prompt reading the values of a
        record to create. """
        try:
            return self._text_chat(prompt, usage)
        except UserError as error:
            raise UserError(self.env._(
                "The values of the record could not be read: %(error)s", error=error.args[0],
            )) from error

    # ------------------------------------------------------------
    # Values, checked as the user asking
    # ------------------------------------------------------------

    @api.model
    def _resolve_value_for_create(self, Model, field, raw, report):
        """ A value read by the AI, as Odoo stores it, with its text shown in the draft;
        ``None`` when it is not valid. Related records are found by name, or by the
        query describing them, among those the user can read.

        :param dict report: ``warnings`` and ``notes`` to show in the draft, and the
            ``usage`` of the AI
        """
        warnings = report['warnings']
        label = field._description_string(self.env)
        if isinstance(raw, models.BaseModel):
            # a record found by the query of a line
            return raw.id, raw.display_name
        try:
            if field.type in ('char', 'text'):
                value = str(raw).strip()[:getattr(field, 'size', None) or MAX_TEXT_LENGTH]
                return (value, value) if value else None
            if field.type == 'integer':
                value = int(float(raw))
                return value, formatLang(self.env, value, digits=0)
            if field.type in ('float', 'monetary'):
                value = float(raw)
                if field.type == 'monetary':
                    return value, format_amount(self.env, value, self.env.company.currency_id)
                return value, formatLang(self.env, value)
            if field.type == 'boolean':
                value = raw if isinstance(raw, bool) else str(raw).strip().lower() in ('true', 'yes', '1')
                return value, self.env._("Yes") if value else self.env._("No")
            if field.type == 'date':
                value = fields.Date.to_date(str(raw).strip()[:10])
                return fields.Date.to_string(value), format_date(self.env, value)
            if field.type == 'datetime':
                text = str(raw).strip().replace('T', ' ')
                # a day without a time ("tomorrow"): at the start of that day
                local = datetime.strptime(text[:16], '%Y-%m-%d %H:%M') if len(text) > 10 \
                    else datetime.strptime(text[:10], '%Y-%m-%d')
                value = pytz.timezone(self.env.user.tz or 'UTC').localize(local).astimezone(pytz.utc).replace(tzinfo=None)
                return fields.Datetime.to_string(value), format_datetime(self.env, value)
        except (TypeError, ValueError):
            warnings.append(self.env._("\"%(value)s\" is no valid %(field)s.", value=raw, field=label))
            return None
        if field.type == 'selection':
            text = str(raw).strip().lower()
            for key, value_label in field._description_selection(self.env):
                if text in (str(key).lower(), str(value_label).lower()):
                    return key, value_label
            warnings.append(self.env._("\"%(value)s\" is no valid %(field)s.", value=raw, field=label))
            return None
        if (new_name := _get_new(raw)) and not self._is_said_new(new_name):
            # marked as new by the AI only: looked for as any name, created when no record bears it
            raw = new_name
        if field.type == 'many2one':
            if query := _get_query(raw):
                record = self._find_records_by_query(field, query, report, ask_count=False)[:1]
            elif new_name := _get_new(raw):
                # marked as new by the AI: the record bearing that very name, when there is one, else a new one
                if existing := self._find_existing_record(field, new_name, report):
                    return existing.id, existing.display_name
                return self._plan_new_record(field, new_name, report)
            elif planned := self._find_planned_record(field, str(raw), report):
                return planned
            else:
                choices = report.setdefault('choices', [])
                asked = len(choices)
                record = self._find_record_for_create(field, str(raw), warnings, warn_missing=report['steps'] is None,
                                                      choices=choices)
                if not record and len(choices) > asked:
                    # several records may be meant: none is created, the user chooses
                    return None
                if not record and report['steps'] is not None:
                    return self._plan_new_record(field, str(raw), report)
            if record and field.comodel_name == 'res.partner' and \
                    record.commercial_partner_id.id == self.env.context.get('ai_chat_exclude_partner'):
                warnings.append(self.env._(
                    "%(field)s: %(name)s is your own company, not the other party of the document: choose it in the "
                    "form.", field=label, name=record.display_name,
                ))
                return None
            return (record.id, record.display_name) if record else None
        if field.type == 'many2many':
            if query := _get_query(raw):
                records = self._find_records_by_query(field, query, report, count=_get_query_count(raw))
                return ([Command.set(records.ids)], ", ".join(records.mapped('display_name'))) if records else None
            # ids of existing records, and references to the steps creating the new ones
            ids, names = [], []
            for name in (raw if isinstance(raw, list) else [raw])[:MAX_LINES]:
                new_name = _get_new(name)
                if new_name and not self._is_said_new(new_name):
                    name, new_name = new_name, None
                if not new_name and (planned := self._find_planned_record(field, str(name), report)):
                    ids.append(planned[0])
                    names.append(planned[1])
                    continue
                choices = report.setdefault('choices', [])
                asked = len(choices)
                record = self._find_existing_record(field, new_name, report) if new_name \
                    else self._find_record_for_create(field, str(name), warnings, warn_missing=report['steps'] is None,
                                                      choices=choices)
                if len(choices) > asked:
                    continue
                if record:
                    ids.append(record.id)
                    names.append(record.display_name)
                elif report['steps'] is not None and (planned := self._plan_new_record(
                    field, new_name or str(name), report,
                )):
                    ids.append(planned[0])
                    names.append(planned[1])
            return ([Command.set(ids)], ", ".join(names)) if ids else None
        return None

    @api.model
    def _plan_new_record(self, field, name, report):
        """ A step creating the record a relational field links to, that does not exist
        yet: the draft of the record, read from the request too.

        :return: ``({"$step": index of the step}, text shown)``, or ``None`` when it
            can not be created
        """
        Comodel = self.env[field.comodel_name]
        label = field._description_string(self.env)
        name = name.strip()[:100]
        steps = report['steps']
        if steps is None or not name or not self._can_create(Comodel._name):
            report['warnings'].append(self.env._(
                "No %(field)s matching \"%(name)s\" was found.", field=label, name=name,
            ))
            return None
        index = self._find_planned_step(Comodel._name, name, steps)
        if index is None and not _keywords(name):
            # no name at all ("him", "the same"): no record made up for it
            report['warnings'].append(self.env._(
                "No %(field)s matching \"%(name)s\" was found.", field=label, name=name,
            ))
            return None
        if index is None and self._is_line_model(Comodel):
            # a line of a document (an order line): it exists only in its document, never made up for a value
            report['warnings'].append(self.env._(
                "No %(field)s matching \"%(name)s\" was found.", field=label, name=name,
            ))
            return None
        if index is None and not self._is_said_new(name) and (
                self._is_configuration_model(Comodel._name) or self._is_settings_model(Comodel._name)):
            # a tax, a unit, a stage: set up in the configuration, not made up to fill a value
            report['warnings'].append(self.env._(
                "No %(field)s matching \"%(name)s\" exists: choose one in the form if needed.", field=label, name=name,
            ))
            return None
        if index is None and any((step.get('new_name') or '').strip().lower() == name.lower() for step in steps):
            # the name of another record the request creates ("a timesheet for the project Cybrosys" is for
            # no new customer Cybrosys)
            return None
        if index is None:
            if len(steps) >= MAX_NEW_RECORDS:
                report['warnings'].append(self.env._(
                    "No %(field)s matching \"%(name)s\" was found, and the request already creates %(count)s "
                    "other records: create it first.", field=label, name=name, count=len(steps),
                ))
                return None
            step = self._build_draft(report['request'], Comodel._name, Comodel._description, report['usage'],
                                     new_name=name)
            # shown in the next steps until it is created, then replaced by the record
            step.update(new_name=name, placeholder=self.env._("%s (new)", name))
            steps.append(step)
            index = len(steps) - 1
        return self._step_reference(index, Comodel._name, steps), steps[index]['placeholder']

    @api.model
    def _is_said_new(self, name):
        """ Whether the request says a record does not exist yet ("the new customer X"),
        as the agent read it too: the AI reading values may say so of another record. """
        intent = self._get_intent()
        if not intent.get('routed'):
            return True
        name = str(name).strip().lower()
        return any(found.get('new') and (found['text'].lower() in name or name in found['text'].lower())
                   for found in intent.get('names') or [])

    @api.model
    def _find_existing_record(self, field, name, report):
        """ The record bearing exactly a name the AI marked as new: the request names it,
        it is not to be created twice. """
        return self._find_record_for_create(field, name, [], warn_missing=False, exact_only=True) \
            or self.env[field.comodel_name]

    @api.model
    def _find_planned_step(self, model_name, name, steps):
        """ The index of the step of a plan creating a record of a model with a name,
        or of a model stored with it (a product template, for a field linking to product
        variants). """
        name = name.strip().lower()
        family = self._get_model_family(model_name)
        return next((
            index for index, step in enumerate(steps)
            if step['model'] in family and name and (step.get('new_name') or '').strip().lower() == name
        ), None)

    @api.model
    def _step_reference(self, index, model_name, steps):
        """ The reference to the record a step creates, for a field linking to records
        of ``model_name``. """
        if steps[index]['model'] == model_name:
            return {'$step': index}
        return {'$step': index, '$as': model_name}

    @api.model
    def _find_planned_record(self, field, name, report):
        """ The record a relational field links to by its name, when a step of the plan
        creates it: the request asks for it before ("a task in that project"), so it is
        linked even if a record of that name already exists.

        :return: ``({"$step": index of the step}, text shown)``, or ``None``
        """
        if not report['steps']:
            return None
        index = self._find_planned_step(field.comodel_name, name, report['steps'])
        return None if index is None else (
            self._step_reference(index, field.comodel_name, report['steps']), report['steps'][index]['placeholder'])

    @api.model
    def _find_records_by_query(self, field, query, report, count=False, ask_count=True):
        """ The records a request describes for a relational field ("my top 5 selling
        products"), found by asking that description to the assistant, as the user.

        :param int count: the number of records to find, as the AI read it in the request
            (or the number of lines it gave that description to)
        :param bool ask_count: whether the AI is asked that number when it is not known: not
            for a field holding a single record ("our biggest customer")
        """
        Comodel = self.env[field.comodel_name]
        label = field._description_string(self.env)
        query = str(query).strip()[:200]
        # the AI may give a plain name as a description ("Desk A"): the record bearing it, or the records
        # the user is to choose among when several bear it
        choices = report.setdefault('choices', [])
        asked = len(choices)
        if record := self._find_record_for_create(field, query, report['warnings'], warn_missing=False,
                                                  exact_only=True, choices=choices):
            return record
        if len(choices) > asked:
            return Comodel
        # the description, understood by the agent as any question; the number of records the request asks
        # for: the one the AI read with the description, else the one the description says ("top 5 ..."),
        # else the AI is asked to read it in the request
        intent = self._understand(query, report['usage'])
        limit = intent.get('limit') or False
        if count and count != limit:
            limit = count
        elif not limit and ask_count:
            limit = self._ask_query_count(report.get('request'), query, report['usage'])
        try:
            with self.env.cr.savepoint():
                result = self.with_context(
                    ai_chat_intent={**intent, 'limit': limit}, ai_chat_data_only=True,
                )._answer_data(query, None, report['usage']).get('result') or {}
        except (UserError, AccessError) as error:
            report['warnings'].append(self.env._(
                "The %(field)s described as \"%(query)s\" could not be found: %(error)s",
                field=label, query=query, error=error.args[0] if error.args else error,
            ))
            return Comodel
        # list answers show records of their model, grouped answers the records they are grouped by
        result_model = result.get('row_model') or (result.get('model') if result.get('type') == 'table' else False)
        ids = [row['id'] for row in result.get('rows') or [] if row.get('id')] if result_model else []
        records = Comodel
        if result_model == Comodel._name:
            records = Comodel.browse(ids).exists()
        elif result_model in Comodel._inherits:
            # e.g. product templates, for a field linking to product variants: their first variant
            link = Comodel._inherits[result_model]
            for record_id in ids:
                records |= Comodel.search([(link, '=', record_id)], limit=1)
        elif result_model and (link := self._get_link_field(self.env[result_model], Comodel._name)):
            # records linking to the ones asked: the lines of an order, for "the products of S00006"
            records = self.env[result_model].browse(ids).exists().mapped(link)
        if not records:
            report['warnings'].append(self.env._(
                "No %(field)s described as \"%(query)s\" was found.", field=label, query=query,
            ))
            return Comodel
        # never more records than the description counts ("top selling five products")
        if limit:
            records = records[:limit]
        report['notes'].append(self.env._(
            "%(field)s from \"%(query)s\": %(records)s",
            field=label, query=query, records=", ".join(records.mapped('display_name')),
        ))
        return records

    @api.model
    def _ask_query_count(self, request, description, usage):
        """ The number of records described as ``description`` a request asks for, read
        by the AI wherever the request says it ("our most selling 5 products", "the
        least sold products. Five products, three of each"); ``False`` when it gives
        none. """
        if not request:
            return False
        answer = self._ask_json(
            "A user asks the Odoo business software to create a record. Read in the request how many records "
            f"described as \"{description}\" it asks for, wherever it says it (before, inside or after the "
            "description, in digits or in words). A quantity of each record is no count of records. Reply with ONLY "
            "minified JSON, no text: {\"count\": <the number, or null when the request gives none>}\n"
            f"Request: {request}", usage,
        )
        return _get_query_count({'$count': answer.get('count')})

    @api.model
    def _find_record_for_create(self, field, text, warnings, warn_missing=True, exact_only=False, choices=None):
        """ The record a name given for a relational field stands for, among those the
        user can read: the one with that very name, else the only one matching it (also
        word by word: "64 gb" for "64GB"), unless ``exact_only``.

        :param list choices: when given, several records matching the name are not chosen
            among: they are added to it, for the user to choose, and none is returned
        """
        Comodel = self.env[field.comodel_name]
        text = text.strip()[:100]
        if not text:
            return Comodel
        label = field._description_string(self.env)
        found = Comodel.name_search(text, limit=MAX_CHOICES)
        if not found and ('(' in text or '[' in text or ' ' in text):
            # the full name of a variant ("Large Desk (Wood)", "[E-COM13] Conference Chair (Aluminium)"): the
            # records named by its first words, the one of that very name among them
            base = re.sub(r'^\[[^\]]*\]\s*|\s*\(.*$', '', text).strip()
            # a code written before the name without brackets ("E-COM13 Conference Chair")
            base = re.sub(r'^\S*\d\S*\s+(?=\S)', '', base).strip() or base or text
            wanted = _plain(text)
            found = [(record_id, name) for record_id, name in Comodel.name_search(base, limit=MAX_CHOICES * 4)
                     if _plain(name) == wanted or _plain(re.sub(r'^\[[^\]]*\]\s*', '', name)) == wanted]
            if found:
                return Comodel.browse(found[0][0])
        if not found and not exact_only and len(words := [word for word in _words(text) if len(word) > 1]) > 1:
            # the words of the name, wherever they are: "sandisk ultra 64 gb" for "SanDisk Ultra 64GB"
            try:
                matching = Comodel.search(Domain.AND([[('display_name', 'ilike', word)] for word in words]),
                                          limit=MAX_CHOICES)
                found = [(record.id, record.display_name) for record in matching]
            except (AccessError, UserError, ValueError):
                found = []
        if not found:
            if warn_missing:
                warnings.append(self.env._("No %(field)s matching \"%(name)s\" was found.", field=label, name=text))
            return Comodel
        # "[LAP-001] Dell Latitude" is named "Dell Latitude": its internal reference is no part of its name
        exact = [record_id for record_id, name in found
                 if _plain(text) in (_plain(name), _plain(re.sub(r'^\[[^\]]*\]\s*', '', name)))]
        if exact:
            return Comodel.browse(exact[0])
        if len(found) > 1 and choices is not None:
            # several records may be meant (the variants of a product, two contacts of close names): the user
            # chooses, even when only an exact name would do
            choices.append({'field': label, 'text': text, 'options': [name for _id, name in found]})
            return Comodel
        if exact_only:
            return Comodel
        record = Comodel.browse(found[0][0])
        if len(found) > 1:
            warnings.append(self.env._(
                "Several %(field)s match \"%(name)s\": %(chosen)s was chosen.",
                field=label, name=text, chosen=record.display_name,
            ))
        return record

    @api.model
    def _resolve_lines(self, field, sub_fields, raw, report):
        """ The lines of a one2many field, as creation commands, and the table showing
        them in the draft. A line whose link is described by a query becomes one line
        per record found; a line whose linked record is not found is left out, rather
        than created without it (a sales order line without its product). """
        Line = self.env[field.comodel_name]
        rows, commands, used = [], [], []
        raw_lines = []
        queried_lines = []
        for raw_line in (raw if isinstance(raw, list) else [])[:MAX_LINES]:
            if not isinstance(raw_line, dict):
                continue
            queried = next((
                name for name in sub_fields
                if Line._fields[name].type == 'many2one' and _get_query(raw_line.get(name))
            ), None)
            raw_lines.append(raw_line)
            queried_lines.append(queried and (queried, _get_query(raw_line[queried]).strip().lower()))
        # the AI may repeat a description on as many lines as the records it counts ("five of the
        # least selling products" as 5 lines): it describes these records once, not once per line
        repeats = {key: queried_lines.count(key) for key in queried_lines if key}
        expanded, seen = [], set()
        for raw_line, key in zip(raw_lines, queried_lines):
            if not key:
                expanded.append(raw_line)
                continue
            if key in seen:
                continue
            seen.add(key)
            queried = key[0]
            records = self._find_records_by_query(
                Line._fields[queried], _get_query(raw_line[queried]), report,
                count=_get_query_count(raw_line[queried]) or (repeats[key] if repeats[key] > 1 else False),
            )
            expanded += [{**raw_line, queried: record} for record in records]
        raw_lines = expanded
        for raw_line in raw_lines[:MAX_LINES]:
            line_values, cells, is_complete = {}, {}, True
            for name in sub_fields:
                if raw_line.get(name) in (None, '', []):
                    continue
                sub_field = Line._fields[name]
                resolved = self._resolve_value_for_create(Line, sub_field, raw_line[name], report)
                if resolved is None:
                    is_complete = is_complete and not sub_field.relational
                    continue
                line_values[name], cells[name] = resolved
            if not is_complete:
                report['warnings'].append(self.env._(
                    "A line of %(field)s was left out, as a record it links to was not found.",
                    field=field._description_string(self.env),
                ))
                continue
            used += [name for name in line_values if name not in used]
            if line_values:
                commands.append(Command.create(line_values))
                rows.append(cells)
        table = {
            'label': field._description_string(self.env),
            'columns': [Line._fields[name]._description_string(self.env) for name in used],
            'rows': [[cells.get(name, '') for name in used] for cells in rows],
        }
        return commands, table

    @api.model
    def _get_missing_fields(self, Model, values):
        """ The labels of the required fields that neither the request nor a default
        value fills. """
        required = [
            name for name, field in Model._fields.items()
            if field.required and not field.compute and not field.related and name not in values
            and name not in SKIPPED_FIELD_NAMES and name not in Model._inherits.values()
            # lines Odoo fills itself (the variants of a product)
            and field.type != 'one2many'
        ]
        defaults = Model.default_get(required) if required else {}
        return [
            Model._fields[name]._description_string(self.env) for name in required
            if defaults.get(name) in (None, False)
        ]

    # ------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------

    @api.model
    def _create_from_draft(self, draft):
        """ Create the record of a draft, as the current user. """
        model_name = draft.get('model')
        if not draft.get('values'):
            raise UserError(self.env._("This draft has no value: open it in the form to fill it in."))
        if not self._can_create(model_name):
            raise AccessError(self.env._("You are not allowed to create %s records.", draft.get('model_label')))
        try:
            with self.env.cr.savepoint():
                record = self.env[model_name].with_context(**(draft.get('context') or {})).create(
                    draft.get('values') or {})
                # computed and constrained values are checked now, to report errors here
                self.env.flush_all()
        except (UserError, AccessError):
            raise
        except Exception as error:
            _logger.info("AI Chat Pro: %s could not be created from a draft: %s", model_name, error)
            raise UserError(self.env._(
                "The %(label)s could not be created. Open it in the form to complete it.",
                label=draft.get('model_label'),
            ))
        return record
