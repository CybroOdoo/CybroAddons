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

import logging
import re
from datetime import date, datetime

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .ai_chat_creator import MAX_LINES

_logger = logging.getLogger(__name__)

# a reference holding a number: S00100, INV/2026/00012, P00042, WH/OUT/00007
NUMBERED_RE = re.compile(r"[A-Za-z]*[A-Za-z0-9]*[/._-]?\d[\w/.-]*")
# what the draft of a copy shows of the record copied
MAX_SHOWN_COPIED_FIELDS = 8
MAX_COPIED_COLUMNS = 5


class AiChatAssistant(models.AbstractModel):
    """ Records duplicated from the chat: "duplicate S00100", "create a sales order
    like S00100 for Azure Interior". The record is copied as Odoo does it (the
    Duplicate action), with the changes the request asks for, after the user
    confirms the draft of the copy. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _find_record_to_duplicate(self, question, reference):
        """ The record a request refers to, among the records the user can read and
        create: the one bearing exactly the reference in the models the request names,
        then, for a numbered reference (S00100), in all the models of the menus; only
        then the one that comes close in the models the request names. ``None`` when not
        found. """
        texts = self._get_reference_texts(reference)
        if not texts:
            return None
        candidates = self._find_candidates(self._get_question_keywords(question))[:5]
        for candidate in candidates:
            if found := self._search_reference(candidate['model'], texts, candidate.get('label'), exact_only=True):
                return found
        numbered = [text for text in texts if NUMBERED_RE.fullmatch(text) and any(c.isdigit() for c in text)]
        if numbered:
            tried = {candidate['model'] for candidate in candidates}
            for model_name, label, _words, menus in self._get_model_catalog():
                if menus and model_name not in tried:
                    if found := self._search_reference(model_name, numbered, label, exact_only=True):
                        return found
        for candidate in candidates:
            if found := self._search_reference(candidate['model'], texts, candidate.get('label')):
                return found
        return None

    @api.model
    def _get_reference_texts(self, reference):
        """ The names a reference may give a record, most precise first: its numbered
        words ("S00100" in "sale order S00100"), then the reference as the agent read it,
        then without its first words ("John Smith" in "contact John Smith"). """
        words = reference.split()
        texts = [word.strip('#') for word in words if any(char.isdigit() for char in word)]
        texts += [" ".join(words[start:]).strip() for start in range(len(words))]
        return list(dict.fromkeys(text for text in texts if len(text) > 1))

    @api.model
    def _search_reference(self, model_name, texts, label=None, exact_only=False):
        """ The record of a model named by one of the texts, that the user can copy. """
        if not self._can_create(model_name):
            return None
        Model = self.env[model_name]
        for text in texts:
            try:
                found = Model.name_search(text, limit=5)
            except (AccessError, UserError, ValueError):
                return None
            exact = [record_id for record_id, name in found if name.strip().lower() == text.lower()]
            if exact or (found and not exact_only and len(found) == 1 and len(text) > 3):
                return {'record': Model.browse((exact or [found[0][0]])[0]), 'label': label or Model._description}
        return None

    @api.model
    def _draft_copy(self, question, found, reference, usage):
        """ The draft of the copy of a record, with the changes the request asks for. """
        source, label = found['record'], found['label']
        Model = self.env[source._name]
        create_fields = self._get_create_fields(Model)
        # the changes: values the request gives, read as for a new record, the copy being said
        changes = self._build_draft(
            f"{question}\n(The new {Model._description} is a copy of \"{source.display_name}\": give only the "
            f"values the request changes. \"{reference}\" is the record copied, not a value.)",
            Model._name, label, usage, warn_dropped=False,
        )
        # a change is a value other than the one of the record copied, and never its reference: "duplicate
        # S00100" gives the copy a number of its own, not "S00100" again
        values = {name: value for name, value in changes['values'].items()
                  if not self._is_unchanged(source, name, value, reference)}
        kept_labels = {Model._fields[name]._description_string(self.env) for name in values}
        changes['fields'] = [field for field in changes['fields'] if field['label'] in kept_labels]
        shown = [{'label': self.env._("Copy of"), 'value': source.display_name}]
        changed = {field['label'] for field in changes['fields']}
        shown += changes['fields']
        # the values copied that a new record would not get anyway: its defaults say nothing of the copy
        copied = [
            name for name, sub_fields in create_fields.items()
            if not sub_fields and Model._fields[name].copy and source[name]
            and Model._fields[name]._description_string(self.env) not in changed
        ]
        # a blank new record, with its defaults and the values computed from them (the company's options)
        blank = Model.new(Model.default_get(list(create_fields))) if copied else Model
        for name in copied:
            field = Model._fields[name]
            try:
                same = blank[name] == source[name]
            except Exception:  # noqa: BLE001 - a value that can not be computed without more values
                same = False
            if same:
                continue
            shown.append({'label': field._description_string(self.env),
                          'value': self._format_copied_value(source, field)})
            if len(shown) > MAX_SHOWN_COPIED_FIELDS:
                break
        lines = self._get_copied_lines(source, create_fields)
        for table in changes['lines']:
            table = dict(table, label=self.env._("%s (added)", table['label']))
            lines.append(table)
        title = self.env._("Copy of %(label)s %(name)s", label=label, name=source.display_name)
        draft = {
            'type': 'draft',
            'state': 'draft',
            'model': Model._name,
            'model_label': label,
            'title': title,
            'fields': shown,
            'lines': lines,
            'warnings': [warning for warning in changes['warnings'] if reference.lower() not in warning.lower()],
            'notes': changes['notes'],
            'missing': [],
            'values': values,
            'copy_of': {'id': source.id, 'name': source.display_name},
        }
        content = self.env._(
            "Here is the copy of %(label)s \"%(name)s\" to create. Check it, then create it.",
            label=label, name=source.display_name,
        )
        source_kind = 'openrouter_olg' if usage['ai_called'] else 'olg'
        return {'content': content, 'result': draft, 'source': source_kind}

    @api.model
    def _is_unchanged(self, source, name, value, reference):
        """ Whether a value read for a copy is the reference of the record copied, or
        the value it holds already. """
        field = source._fields[name]
        if field.type == 'one2many':
            return False
        if field.type == 'many2one':
            return isinstance(value, int) and value == source[name].id
        text = str(value).strip().lower()
        return text in {str(reference).strip().lower(), str(source.display_name).strip().lower()} or (
            field.type in ('char', 'text', 'selection') and text == str(source[name] or '').strip().lower())

    @api.model
    def _format_copied_value(self, record, field):
        value = record[field.name]
        if field.type in ('many2one', 'many2many', 'one2many'):
            return ", ".join(value.mapped('display_name'))
        return self._format_field(record, field)

    @api.model
    def _get_copied_lines(self, source, create_fields):
        """ The lines the copy gets, as shown in the draft. """
        tables = []
        for name, sub_fields in create_fields.items():
            field = source._fields[name]
            if field.type != 'one2many' or not field.copy or not source[name]:
                continue
            Line = self.env[field.comodel_name]
            records = source[name][:MAX_LINES]
            # the columns copied, and filled on some line
            used = [
                sub for sub in sub_fields
                if sub in Line._fields and Line._fields[sub].copy
                and any(line[sub] for line in records)
            ][:MAX_COPIED_COLUMNS]
            rows = [[self._format_copied_value(line, Line._fields[sub]) for sub in used] for line in records]
            tables.append({
                'label': self.env._("%s (copied)", field._description_string(self.env)),
                'columns': [Line._fields[sub]._description_string(self.env) for sub in used],
                'rows': rows,
            })
        return tables

    @api.model
    def _create_from_draft(self, draft):
        """ Copy the record of a draft of a copy, as the current user, as the Duplicate
        action of Odoo does: lines asked for are added to the copied ones. """
        if not draft.get('copy_of'):
            return super()._create_from_draft(draft)
        model_name = draft.get('model')
        if not self._can_create(model_name):
            raise AccessError(self.env._("You are not allowed to create %s records.", draft.get('model_label')))
        source = self.env[model_name].browse(draft['copy_of']['id']).exists()
        if not source:
            raise UserError(self.env._("The record to copy no longer exists."))
        source.check_access('read')
        values = dict(draft.get('values') or {})
        added_lines = {name: values.pop(name) for name in list(values)
                       if source._fields[name].type == 'one2many'}
        try:
            with self.env.cr.savepoint():
                record = source.copy(default=values)
                if added_lines:
                    record.write(added_lines)
                self.env.flush_all()
        except (UserError, AccessError):
            raise
        except Exception as error:
            _logger.info("AI Chat Pro: %s could not be copied from a draft: %s", model_name, error)
            raise UserError(self.env._(
                "The copy of %(name)s could not be created. Duplicate it from its form instead.",
                name=draft['copy_of'].get('name'),
            ))
        return record

    @api.model
    def _get_copy_form_values(self, draft):
        """ The values of the copy of a draft, as default values of a new form: the
        values Odoo copies, the changes asked for, and the lines added after the
        copied ones. """
        source = self.env[draft['model']].browse(draft['copy_of']['id']).exists()
        if not source:
            raise UserError(self.env._("The record to copy no longer exists."))
        source.check_access('read')
        changes = dict(draft.get('values') or {})
        added = {name: changes.pop(name) for name in list(changes) if source._fields[name].type == 'one2many'}
        values = source.copy_data(default=changes)[0]
        for name, commands in added.items():
            values[name] = list(values.get(name) or []) + list(commands)
        # dates as text, as the web client reads them
        return {name: _to_json(value) for name, value in values.items() if name in source._fields}


def _to_json(value):
    """ A value of a record, dates as text, also inside the commands of lines. """
    if isinstance(value, datetime):
        return fields.Datetime.to_string(value)
    if isinstance(value, date):
        return fields.Date.to_string(value)
    if isinstance(value, dict):
        return {key: _to_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json(item) for item in value]
    return value
