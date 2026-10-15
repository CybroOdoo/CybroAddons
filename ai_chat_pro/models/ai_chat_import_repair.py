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

import csv
import io
import logging
import re
from datetime import date, datetime

from dateutil import parser as date_parser

from odoo import api, models
from odoo.exceptions import AccessError, UserError

from .ai_chat_assistant import _keywords, _stem, _words
from .ai_chat_creator import _loads_loosely

_logger = logging.getLogger(__name__)

# the values the AI is asked to repair at once, in a few requests at most, and the records it chooses among
REPAIR_BATCH = 40
MAX_REPAIR_CALLS = 6
MAX_CANDIDATES = 6
# new coded records typed by the AI at once, from their name (the type of new accounts)
TYPE_BATCH = 80
# types never given to new records: they change how the record using them works (an entry with an
# off-balance account must only have such accounts)
TYPE_EXCLUDED_OPTIONS = {'off_balance'}
# the menus of a model, and the options in all, the AI chooses the records to import among
MAX_MENU_OPTIONS = 5
MAX_IMPORT_OPTIONS = 14
# a value made of a code, then a name: "1000- Aripero", "ACC-12 Cash"
CODE_RE = re.compile(r'^\s*([A-Za-z]{0,4}[-/]?\d[\w./-]*?)(?:\s*[-–:]\s*|\s+|$)(.*)$')
MAX_DEFAULT_OPTIONS = 15
# test imports: each one drops the rows that still fail, until none does
MAX_REPAIR_ROUNDS = 4
# configuration, never created from a value of a file
NEVER_CREATE_MODELS = {
    'res.country', 'res.country.state', 'res.currency', 'res.company', 'res.users', 'res.groups', 'res.lang',
    'account.tax', 'account.journal', 'account.fiscal.position', 'uom.uom', 'ir.model', 'stock.warehouse',
}
# fields given when a record is created, besides its required ones: its code (accounts)
CREATE_EXTRA_FIELDS = ('code', 'default_code')
MAX_CREATE_FIELDS = 6
TRUE_WORDS = {'1', 'true', 'yes', 'y', 'x', 'on', 't', 'ok', 'active', '✓', '✔'}
FALSE_WORDS = {'0', 'false', 'no', 'n', 'off', 'f', 'inactive', '-'}
NUMBER_RE = re.compile(r'[^\d,.\-()]')
# the options of the cleaned file: values are written as Odoo reads them
CLEAN_OPTIONS = {
    'encoding': 'utf-8', 'separator': ',', 'quoting': '"', 'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M:%S', 'float_thousand_separator': '', 'float_decimal_separator': '.',
    # no 'limit': all the rows are imported (a limit of 0 imports none)
    'advanced': True, 'has_headers': True, 'keep_matches': False, 'sheets': [], 'sheet': '', 'skip': 0,
    'tracking_disable': True, 'import_skip_records': [], 'import_set_empty_fields': [], 'fallback_values': {},
    'name_create_enabled_fields': {},
}
CREATE_TOKEN = '__create__:'


class AiChatAssistant(models.AbstractModel):
    """ The repair of a spreadsheet before it is imported, so that an import is never
    blocked by its values: each column is cleaned as its field reads values (numbers,
    dates, yes/no, options), values linking to records are matched with existing ones
    (or created, or left empty) by the AI, required fields the file lacks get a default,
    and the rows that still fail a test import are left out, with their reason. """
    _inherit = 'ai.chat.assistant'

    # ------------------------------------------------------------
    # Reading the file, choosing the records
    # ------------------------------------------------------------

    @api.model
    def _read_import_rows(self, attachment):
        """ The column names and the rows of a spreadsheet, empty rows left out. """
        importer = self._new_import('res.partner', attachment)
        try:
            _length, rows = importer._read_file(dict(CLEAN_OPTIONS, encoding='', separator='', date_format='',
                                                     datetime_format='', float_thousand_separator=','))
            rows = list(rows)
        except Exception as error:  # noqa: BLE001 - any error of the file's reader
            raise UserError(self.env._("The file could not be read: %s", error))
        if not rows:
            raise UserError(self.env._("The file is empty."))
        headers = [_to_cell(cell).strip() or f"Column {index + 1}" for index, cell in enumerate(rows[0])]
        data = [row for row in rows[1:] if any(_to_cell(cell).strip() for cell in row)]
        return headers, data

    @api.model
    def _choose_import_target(self, question, headers, rows, usage):
        """ The kind of records a file holds, chosen by the AI among the models the user
        can create, from the request and the file itself; and whether each row is a
        record, or a line of a single record (a trial balance: the lines of one
        journal entry).

        :return: ``(candidate, lines field name or False)``, or ``(None, False)``
        """
        words = _keywords(question) | _keywords(" ".join(headers))
        found = [c for c in self._find_candidates(words) if self._can_create(c['model'])][:4]
        named = self._choose_import_model(question, usage)
        if named and named['model'] not in [c['model'] for c in found]:
            found.insert(0, named)
        if not found:
            return None, False
        # each menu of a model is an option: its defaults make other records (a credit note, an entry)
        candidates = self._get_import_menu_options(found)
        options = {}
        for index, candidate in enumerate(candidates):
            Model = self.env[candidate['model']]
            lines = [f"{name} ({Model._fields[name]._description_string(self.env)})"
                     for name in self._get_lines_fields(Model)][:3]
            defaults = ", ".join(f"{key.removeprefix('default_')}={value}"
                                 for key, value in self._get_import_context(candidate).items())
            options[f"option_{index}"] = (
                f"{candidate['label']} [{candidate['model']}]"
                + (f" (menu {candidate['path']})" if candidate.get('path') else " (no menu: the defaults of the record itself)")
                + (f", creating with {defaults}" if defaults else '')
                + (f", fields of lines: {', '.join(lines)}" if lines else '')
            )
        sample = "\n".join(" | ".join(_to_cell(cell)[:40] for cell in row) for row in rows[:3])
        prompt = (
            "A user sends a spreadsheet to Odoo, the business software, with a request. Choose which kind of records "
            "its rows create, among the options, from the request and the columns. Each row is a record (a list of "
            "products, contacts, accounts, invoices), unless the whole file is one document whose rows are its lines: "
            "a trial balance or an opening balance is one journal entry whose rows are its journal items (debit and "
            "credit per account), not invoice lines. Then name its field of lines.\n"
            "Reply with ONLY minified JSON, no text: {\"option\":\"option_N\",\"rows\":\"records\"|\"lines\","
            "\"lines_field\":\"<field>\"|null}\n"
            f"Request: {question}\nColumns: {' | '.join(headers)}\nFirst rows:\n{sample}\nOptions:\n"
            + "\n".join(f"- {key}: {text}" for key, text in options.items())
        )
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage)) or {}
        except UserError as error:
            _logger.info("AI Chat Pro: the records of a file could not be chosen by the AI: %s", error)
            answer = {}
        key = answer.get('option') if isinstance(answer, dict) else None
        chosen = candidates[int(key.removeprefix('option_'))] if key in options else (named or candidates[0])
        Model = self.env[chosen['model']]
        lines_field = False
        if answer.get('rows') == 'lines' and answer.get('option') in options:
            name = answer.get('lines_field')
            field = Model._fields.get(name) if isinstance(name, str) else None
            if field and name in self._get_lines_fields(Model):
                lines_field = name
        # the columns tell too: when the fields of its lines name them better than its own fields
        # (account, debit, credit: the journal items of an entry), the rows are lines
        detected = self._detect_lines_field(Model, headers)
        if detected and (not lines_field or (Model._fields[lines_field].domain and not Model._fields[detected].domain)):
            lines_field = detected
        return chosen, lines_field

    @api.model
    def _get_import_menu_options(self, candidates):
        """ The candidates to import records as, one per menu of their model the user can
        see: Accounting > Journal Entries and Invoicing > Credit Notes create different
        journal entries. """
        menus_by_model = {model_name: menus for model_name, _label, _words, menus in self._get_model_catalog()}
        options = []
        for candidate in candidates:
            menus = menus_by_model.get(candidate['model']) or []
            paths = {candidate.get('path')}
            options.append(candidate)
            if any(self._get_import_context(dict(candidate, context=context)) for _path, _domain, context, *_rest in menus):
                # the records with their own defaults, as an import of the model creates them: a plain journal
                # entry, when the only menus the user sees create invoices and credit notes
                options.append(dict(candidate, path='', domain='', context='', search_view_id=False))
                paths.add('')
            for path, domain, context, search_view_id, _menu_words in menus:
                if path in paths or len(paths) > MAX_MENU_OPTIONS:
                    continue
                paths.add(path)
                options.append(dict(candidate, path=path, domain=domain, context=context, search_view_id=search_view_id))
        return options[:MAX_IMPORT_OPTIONS]

    @api.model
    def _get_lines_fields(self, Model):
        """ The fields of lines of a model an import can fill: its one2many fields of
        business records (not its messages, followers or attachments). """
        return [
            name for name, field in Model._fields.items()
            if field.type == 'one2many' and not field.readonly and field.store is not False
            and not field.comodel_name.startswith(('mail.', 'ir.', 'bus.', 'rating.', 'res.users', 'account.analytic'))
            and self.env[field.comodel_name]._auto and field.inverse_name
        ]

    @api.model
    def _detect_lines_field(self, Model, headers):
        """ The field of lines whose fields name the columns of a file better than the
        fields of the record itself, if any; among fields of lines naming them as well,
        the one showing all the lines (journal items, rather than invoice lines). """
        header_words = [set(map(_stem, _words(header))) for header in headers]

        def score(fields_):
            labels = [set(map(_stem, _words(f._description_string(self.env)))) | {f.name}
                      for f in fields_ if f.type not in ('one2many',)]
            return sum(1 for words in header_words if any(words & label for label in labels))

        create_fields = self._get_create_fields(Model)
        own = score([Model._fields[name] for name in create_fields if name in Model._fields])
        best, best_score = False, 0
        for name in self._get_lines_fields(Model):
            field = Model._fields[name]
            Line = self.env[field.comodel_name]
            line_fields = [f for f in Line._fields.values()
                           if f.store and not f.readonly and f.name not in ('id', field.inverse_name)][:80]
            current = score(line_fields)
            # fields of lines showing all of them (no domain) first
            if current > best_score or (current == best_score and best and Model._fields[best].domain and not field.domain):
                best, best_score = name, current
        return best if best_score >= 2 and best_score > own else False

    # ------------------------------------------------------------
    # Repair
    # ------------------------------------------------------------

    @api.model
    def _get_import_field(self, model_name, path):
        """ The field a path of an import fills, and the model it belongs to; ``None``
        for the ids of records (``id``, ``partner_id/id``). """
        names = path.split('/')
        Model = self.env[model_name]
        for name in names[:-1]:
            field = Model._fields.get(name)
            if not field or not field.relational:
                return None, None
            if field.type != 'one2many':
                # partner_id/id, partner_id/.id: an id, kept as given
                return None, None
            Model = self.env[field.comodel_name]
        field = Model._fields.get(names[-1])
        return (field, Model) if field and names[-1] not in ('id', '.id') else (None, None)

    @api.model
    def _repair_import(self, question, model_name, headers, rows, import_fields, context, usage, lines_field=False):
        """ The plan of an import that is not blocked by its values.

        :return: ``{paths, rows, row_numbers, creates, fixes, skipped}``: the columns
            (import paths) and cleaned rows to import, the number in the file of each
            row, the records to create first (``{path: [names]}``), and what was changed
        """
        columns = [(index, path) for index, path in enumerate(import_fields) if path]
        fixes = []
        paths = []
        data = [[] for _row in rows]
        unresolved = {}  # position: (field, Model, {value: [candidates]}, may create)
        creates = {}
        for position, (index, path) in enumerate(columns):
            field, Model = self._get_import_field(model_name, path)
            cells = [_to_cell(row[index]) if index < len(row) else '' for row in rows]
            if field is None:
                paths.append(path)
                for row_values, cell in zip(data, cells):
                    row_values.append(cell)
                continue
            cleaned, emptied, pending = self._clean_column(field, cells)
            if emptied:
                fixes.append({'kind': 'empty', 'text': self.env._(
                    "%(field)s: %(count)s values that are no valid %(type)s were left empty (%(examples)s).",
                    field=field._description_string(self.env), count=len(emptied), type=field.type,
                    examples=", ".join(f"'{value}'" for value in list(dict.fromkeys(emptied))[:3]),
                )})
            if field.relational:
                # records linked by id: matched now, so that no name is matched twice
                path = path + '/.id' if field.type != 'one2many' else path
            paths.append(path)
            if pending:
                unresolved[len(paths) - 1] = (field, Model, pending, self._get_create_spec(field))
            for row_values, cell in zip(data, cleaned):
                row_values.append(cell)
        # values the AI repairs, and the defaults of required fields the file lacks
        defaults = self._get_missing_required_fields(model_name, paths, context, lines_field)
        if unresolved or defaults:
            # the other texts of the row of a value: what names a record created from a code alone
            descriptions = {
                position: {value: next((cell for index, cell in enumerate(row) if index != position and cell
                                        and _parse_number(cell) is None and CREATE_TOKEN not in cell), '')
                           for value in pending
                           for row in [next((row for row in data if value in row[position].split(',')), [])]}
                for position, (_field, _Model, pending, _may_create) in unresolved.items()
            }
            decisions = self._ask_import_repairs(question, model_name, headers, columns, paths, unresolved, defaults,
                                                 usage, descriptions)
            for position, (field, Model, pending, may_create) in unresolved.items():
                answers = self._check_matches(field, pending, decisions['values'].get(position, {}))
                for value, candidates in pending.items():
                    decision = answers.get(value) or {'empty': True}
                    replacement, fix, values = self._apply_repair(field, value, candidates, may_create, decision, Model)
                    if replacement.startswith(CREATE_TOKEN):
                        creates.setdefault(paths[position], []).append({'value': value, 'values': values})
                    fixes.append(fix)
                    for row_values in data:
                        row_values[position] = _replace_value(row_values[position], value, replacement, field)
            for name, (value, text) in decisions['defaults'].items():
                path = name + ('/.id' if self.env[model_name]._fields[name].relational else '')
                paths.append(path)
                for number, row_values in enumerate(data):
                    # the values of the record of the lines are written on its first row only
                    row_values.append(value if not lines_field or number == 0 else '')
                fixes.append({'kind': 'default', 'text': self.env._(
                    "%(field)s, required and not in the file: set to %(value)s.",
                    field=self.env[model_name]._fields[name]._description_string(self.env), value=text,
                )})
            for name in set(defaults) - set(decisions['defaults']):
                fixes.append({'kind': 'missing', 'text': self.env._(
                    "%s is required and not in the file: no value could be chosen for it.",
                    self.env[model_name]._fields[name]._description_string(self.env),
                )})
        self._complete_import_plan(question, model_name, headers, rows, columns, paths, data, creates, fixes,
                                   lines_field, usage)
        return {
            'paths': paths, 'rows': data, 'row_numbers': list(range(2, len(rows) + 2)), 'creates': creates,
            'fixes': fixes, 'skipped': [], 'lines_field': lines_field,
        }

    @api.model
    def _ask_json(self, prompt, usage):
        """ The JSON object the AI writing answers replies to a prompt, empty if none. """
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage))
        except UserError as error:
            _logger.info("AI Chat Pro: no answer of the AI for an import: %s", error)
            return {}
        return answer if isinstance(answer, dict) else {}

    @api.model
    def _complete_import_plan(self, question, model_name, headers, rows, columns, paths, data, creates, fixes,
                              lines_field, usage):
        """ What the values of a file do not say, asked to the AI at once: when the file
        is one record (a trial balance), the values of that record the request or the
        file name state (its date: "as at 31.12.2025"); and the kind of the records
        created from values made of a code (the type of new accounts), from their name and
        row, rather than the default of the record. """
        Model = self.env[model_name]
        record_fields = {}
        if lines_field:
            for name in self._get_create_fields(Model):
                field = Model._fields.get(name)
                # its number or name is given by Odoo (a sequence), never by a file name
                if field and field.type in ('date', 'datetime', 'char') and not field.readonly and name not in paths \
                        and name not in (lines_field, Model._rec_name) and len(record_fields) < 8:
                    record_fields[name] = field
        typed = {}
        for path, records in creates.items():
            field, _Owner = self._get_import_field(model_name, path.removesuffix('/.id'))
            Comodel = self.env[field.comodel_name]
            kind = next((f for f in Comodel._fields.values() if f.type == 'selection' and f.required and f.store
                         and not (f.compute and f.readonly) and f.name not in ('state',)), None)
            coded = [record for record in records if _get_code(record['values'].get('name', ''))]
            if kind and coded:
                position = paths.index(path)
                typed[position] = (Comodel, kind, coded)
        if not record_fields and not typed:
            return
        answer = {}
        if record_fields:
            described = ", ".join(f"{name} ({field._description_string(self.env)}, {field.type})"
                                  for name, field in record_fields.items())
            answer.update(self._ask_json(
                f"A spreadsheet is imported into Odoo as one {Model._description}, its rows are its lines. Give the "
                f"values of the record itself that the request or the file name state, and only those (the date of a "
                f"balance \"as at 31.12.2025\" is 2025-12-31), among the fields: {described}.\n"
                "Reply with ONLY minified JSON, no text: {\"record\":{\"<field>\":\"<value>\"}}\n"
                f"Request: {question}", usage,
            ))
        types = {}
        for position, (Comodel, kind, coded) in typed.items():
            options = ", ".join(f"{key}={label}" for key, label in kind._description_selection(self.env)
                                if key not in TYPE_EXCLUDED_OPTIONS)
            for start_index in range(0, len(coded), TYPE_BATCH):
                lines = []
                for record in coded[start_index:start_index + TYPE_BATCH]:
                    row = next((row for row in data if CREATE_TOKEN + record['value'] in row[position]), None)
                    texts = [cell for index, cell in enumerate(row or []) if index != position and cell
                             and _parse_number(cell) is None][:2]
                    lines.append(f"{_get_code(record['values']['name'])}: {record['values']['name']} | {' | '.join(texts)}")
                batch = self._ask_json(
                    f"New {Comodel._description} records are imported into Odoo. Give the "
                    f"{kind._description_string(self.env)} of each, from its name and the other values of its row "
                    f"(\"Leasehold Improvements\" is a fixed asset, \"Bank Charges\" an expense, \"Accounts Payable\" "
                    f"payable, \"Sales\" income).\nOptions: {options}\n"
                    "Reply with ONLY minified JSON, no text: {\"types\":{\"<code>\":\"<option>\"}}\n"
                    "Records (code: code and name | other values of its row):\n" + "\n".join(lines), usage,
                )
                if isinstance(batch.get('types'), dict):
                    types.setdefault(position, {}).update({str(code): str(value) for code, value in batch['types'].items()})
        answer['types'] = types
        record = answer.get('record') if isinstance(answer.get('record'), dict) else {}
        for name, field in record_fields.items():
            value = record.get(name)
            if not value:
                continue
            if field.type in ('date', 'datetime'):
                parsed = _parse_date(str(value))
                if not parsed:
                    continue
                value = parsed.strftime('%Y-%m-%d' if field.type == 'date' else '%Y-%m-%d %H:%M:%S')
            value = str(value).strip()[:200]
            paths.append(name)
            for number, row in enumerate(data):
                row.append(value if number == 0 else '')
            fixes.append({'kind': 'default', 'text': self.env._(
                "%(field)s of the %(record)s set to %(value)s, as the request or the file name says.",
                field=field._description_string(self.env), record=Model._description, value=value,
            )})
        for position, (Comodel, kind, coded) in typed.items():
            keys = {str(key) for key, _label in kind._description_selection(self.env)} - TYPE_EXCLUDED_OPTIONS
            labels = dict(kind._description_selection(self.env))
            column_types = answer['types'].get(position) or {}
            counted = {}
            for record in coded:
                value = column_types.get(_get_code(record['values']['name']))
                if value in keys:
                    record['set'] = {kind.name: value}
                    counted[value] = counted.get(value, 0) + 1
            if counted:
                fixes.append({'kind': 'create', 'text': self.env._(
                    "%(field)s of the new %(records)s, from their names: %(counts)s.",
                    field=kind._description_string(self.env), records=Comodel._description,
                    counts=", ".join(f"{count} {labels.get(value, value)}" for value, count in counted.items()),
                )})

    @api.model
    def _clean_column(self, field, cells):
        """ The values of a column as its field reads them.

        :return: ``(cleaned values, values left empty, {value to repair: candidates})``
        """
        cleaned, emptied, pending = [], [], {}
        selection = None
        if field.type == 'selection':
            selection = field._description_selection(self.env)
        cache = {}
        for cell in cells:
            value = cell.strip()
            if not value:
                cleaned.append('')
                continue
            if field.type in ('integer', 'float', 'monetary'):
                number = _parse_number(value)
                if number is None:
                    emptied.append(value)
                cleaned.append('' if number is None else (str(int(number)) if field.type == 'integer' else repr(number)))
            elif field.type in ('date', 'datetime'):
                parsed = _parse_date(value)
                if parsed is None:
                    emptied.append(value)
                    cleaned.append('')
                else:
                    cleaned.append(parsed.strftime('%Y-%m-%d' if field.type == 'date' else '%Y-%m-%d %H:%M:%S'))
            elif field.type == 'boolean':
                lowered = value.lower()
                if lowered in TRUE_WORDS or lowered in FALSE_WORDS:
                    cleaned.append('1' if lowered in TRUE_WORDS else '0')
                else:
                    emptied.append(value)
                    cleaned.append('')
            elif field.type == 'selection':
                key = next((str(k) for k, label in selection if value.lower() in (str(k).lower(), str(label).lower())), None)
                if key is None:
                    pending.setdefault(value, [{'key': str(k), 'name': str(label)} for k, label in selection])
                cleaned.append(key if key is not None else value)
            elif field.type in ('many2one', 'many2many'):
                names = [name.strip() for name in value.split(',')] if field.type == 'many2many' else [value]
                ids = []
                for name in filter(None, names):
                    if name not in cache:
                        cache[name] = self._match_record_by_name(field, name)
                    if cache[name]:
                        ids.append(str(cache[name]))
                    else:
                        pending.setdefault(name, self._get_record_candidates(field, name))
                        ids.append(name)
                cleaned.append(','.join(ids))
            else:
                cleaned.append(value)
        return cleaned, emptied, pending

    @api.model
    def _match_record_by_name(self, field, name):
        """ The record a name links to, as the import of Odoo matches it: the one bearing
        that very name. """
        try:
            found = self.env[field.comodel_name].name_search(name, operator='=', limit=1)
        except (AccessError, UserError, ValueError):
            return False
        return found[0][0] if found else False

    @api.model
    def _get_record_candidates(self, field, name):
        """ The records a name not found may stand for: those whose name holds it, or its
        words. """
        Comodel = self.env[field.comodel_name]
        found = {}
        words = [word for word in re.findall(r'[\w%.]{2,}', name) if word != name][:3]
        # misspelled names ("Indai"): the records starting like them
        searches = [name] + words + [name[:4], name[:3]]
        for text in searches:
            try:
                for record_id, display_name in Comodel.name_search(text, limit=MAX_CANDIDATES):
                    found.setdefault(record_id, display_name)
            except (AccessError, UserError, ValueError):
                break
            if len(found) >= MAX_CANDIDATES:
                break
        return [{'id': record_id, 'name': display_name} for record_id, display_name in list(found.items())[:MAX_CANDIDATES]]

    @api.model
    def _get_create_spec(self, field):
        """ How the records a field links to may be created from a value of a file:
        ``{'mode': 'name'}`` when a name is enough (tags, categories), ``{'mode':
        'values', 'fields': {name: (label, type, options)}}`` when other values are
        needed (an account: its code and type), ``None`` for configuration (countries,
        taxes) or records needing other records. """
        if field.type not in ('many2one', 'many2many') or field.comodel_name in NEVER_CREATE_MODELS:
            return None
        Comodel = self.env[field.comodel_name]
        if not (Comodel._auto and not Comodel._transient and Comodel.has_access('create')):
            return None
        rec_name = Comodel._fields.get(Comodel._rec_name or '')
        if not rec_name or rec_name.type != 'char':
            return None
        names = [
            name for name, f in Comodel._fields.items()
            if f.required and not f.compute and not f.related
            and name not in (Comodel._rec_name, 'id', 'company_id', 'currency_id') and f.type != 'one2many'
        ]
        defaults = Comodel.default_get(names) if names else {}
        needed = [name for name in names if defaults.get(name) in (None, False)]
        if not needed:
            return {'mode': 'name'}
        needed += [name for name in CREATE_EXTRA_FIELDS if name in Comodel._fields and name not in needed]
        spec = {}
        for name in needed[:MAX_CREATE_FIELDS]:
            f = Comodel._fields[name]
            if f.type == 'selection':
                options = [str(key) for key, _label in f._description_selection(self.env)]
            elif f.type in ('char', 'text', 'integer', 'float', 'monetary', 'boolean', 'date'):
                options = None
            else:
                # a record needing another record is not created from a file
                return None
            spec[name] = (f._description_string(self.env), f.type, options)
        return {'mode': 'values', 'fields': spec}

    @api.model
    def _get_missing_required_fields(self, model_name, paths, context, lines_field):
        """ The required fields of the records the file does not fill, and no default
        value does: ``{name: options}``, options being records or choices to choose
        among (``None`` for a free value). """
        Model = self.env[model_name].with_context(**(context or {}))
        filled = {path.split('/')[0] for path in paths}
        missing = {}
        names = [
            name for name, field in Model._fields.items()
            if field.required and not field.compute and not field.related and name not in filled
            and name not in ('id', 'company_id', 'currency_id', lines_field) and field.type not in ('one2many', 'binary')
        ]
        defaults = Model.default_get(names) if names else {}
        for name in names:
            if defaults.get(name) not in (None, False):
                continue
            field = Model._fields[name]
            if field.type in ('many2one', 'many2many'):
                try:
                    options = [{'id': record_id, 'name': display_name}
                               for record_id, display_name in self.env[field.comodel_name].name_search('', limit=MAX_DEFAULT_OPTIONS)]
                except (AccessError, UserError):
                    options = []
            elif field.type == 'selection':
                options = [{'key': str(key), 'name': str(label)} for key, label in field._description_selection(self.env)]
            else:
                options = None
            missing[name] = options
        return missing

    @api.model
    def _ask_import_repairs(self, question, model_name, headers, columns, paths, unresolved, defaults, usage,
                            descriptions=None):
        """ The decisions of the AI on the values the import can not read, and on the
        defaults of the required fields the file lacks, in batches of values. Values
        made of a code no record holds ("1000- Aripero" in a trial balance, hundreds of
        them) are decided once per column: created as new records, with a unique code
        each, or left empty.

        :return: ``{'values': {position: {value: decision}}, 'defaults': {field: (value, text)}}``
        """
        Model = self.env[model_name]
        coded, items = {}, []
        for position, (field, _Comodel, pending, may_create) in unresolved.items():
            for value, candidates in pending.items():
                code = _get_code(value)
                # a record holding the code as a word ("1000 Cash"), not inside another code ("100001 Bank")
                if may_create and may_create['mode'] == 'name' and code and not any(
                        re.search(rf'(?<![\w.]){re.escape(code)}(?![\w])', str(candidate['name'])) for candidate in candidates):
                    coded.setdefault(position, []).append(value)
                else:
                    items.append((position, value, candidates))
        batches = [items[start:start + REPAIR_BATCH] for start in range(0, len(items), REPAIR_BATCH)][:MAX_REPAIR_CALLS]
        if not batches and (defaults or coded):
            batches = [[]]
        values, raw_defaults, policies = {}, {}, {}
        for number, batch in enumerate(batches):
            answer = self._ask_import_repair_batch(
                question, Model, headers, unresolved, batch, defaults if number == 0 else {},
                coded if number == 0 else {}, usage,
            )
            for key, decisions in (answer.get('values') or {}).items():
                position = _get_position(key)
                if position in unresolved and isinstance(decisions, dict):
                    values.setdefault(position, {}).update(
                        {str(value): decision for value, decision in decisions.items() if isinstance(decision, dict)})
            if number == 0:
                raw_defaults = answer.get('defaults') if isinstance(answer.get('defaults'), dict) else {}
                policies = answer.get('new') if isinstance(answer.get('new'), dict) else {}
        for position, decisions in values.items():
            field, _Comodel, _pending, may_create = unresolved[position]
            named = [value for value, decision in decisions.items()
                     if decision.get('create') is True and may_create and may_create['mode'] == 'name' and _get_code(value)]
            for value, name in self._get_coded_names(field, named, (descriptions or {}).get(position)).items():
                decisions[value] = {'create': {'name': name}}
        for position, coded_values in coded.items():
            create = policies.get(f"column_{position}") is True
            field = unresolved[position][0]
            names = self._get_coded_names(field, coded_values, (descriptions or {}).get(position)) if create else {}
            for value in coded_values:
                values.setdefault(position, {})[value] = {'create': {'name': names[value]}} if create else {'empty': True}
        chosen = {}
        for name, options in defaults.items():
            value = raw_defaults.get(f"default_{name}")
            if value in (None, '', False):
                continue
            if options is None:
                chosen[name] = (str(value), f"\"{value}\"")
                continue
            option = next((o for o in options if str(o.get('id', o.get('key'))) == str(value)), None)
            if option:
                chosen[name] = (str(option.get('id', option.get('key'))), option['name'])
        return {'values': values, 'defaults': chosen}

    @api.model
    def _ask_import_repair_batch(self, question, Model, headers, unresolved, batch, defaults, coded, usage):
        """ One request to the AI: the values of a batch, the defaults of the required
        fields, and whether to create the new coded values of each column. """
        parts = []
        by_column = {}
        for position, value, candidates in batch:
            by_column.setdefault(position, []).append((value, candidates))
        for position in sorted(set(by_column) | set(coded)):
            field, _Comodel, _pending, may_create = unresolved[position]
            label = field._description_string(self.env)
            if not may_create:
                creation = ""
            elif may_create['mode'] == 'name':
                creation = ", a record can be created from the value: {\"create\":true}"
            else:
                described = ", ".join(
                    f"{name} ({flabel}, {kind}" + (f": {'|'.join(options)}" if options else "") + ")"
                    for name, (flabel, kind, options) in may_create['fields'].items()
                )
                creation = (", a record can be created with its values: {\"create\":{\"name\":\"<name>\", "
                            f"<field>: <value>}}}} for the fields {described}")
            lines = [f"Column column_{position} \"{label}\" ({field.type}"
                     + (f" of {self.env[field.comodel_name]._description}" if field.relational else "")
                     + creation + "):"]
            for value, candidates in by_column.get(position, []):
                options = ", ".join(
                    (f"{c['id']}=\"{c['name']}\"" if 'id' in c else f"\"{c['key']}\"={c['name']}") for c in candidates
                ) or "none"
                lines.append(f"  - value \"{value}\": options {options}")
            if position in coded:
                examples = ", ".join(f'"{value}"' for value in coded[position][:8])
                lines.append(f"  - {len(coded[position])} values hold a code no record has (e.g. {examples}): say in "
                             f"\"new\" whether to create them as new records (true), or leave them empty (false)")
            parts.append("\n".join(lines))
        for name, options in defaults.items():
            field = Model._fields[name]
            if options is None:
                parts.append(f"Required field default_{name} \"{field._description_string(self.env)}\" ({field.type}): "
                             "a value that fits all the rows, or null")
            else:
                text = ", ".join((f"{o['id']}=\"{o['name']}\"" if 'id' in o else f"\"{o['key']}\"={o['name']}")
                                 for o in options) or "none"
                parts.append(f"Required field default_{name} \"{field._description_string(self.env)}\" ({field.type}): "
                             f"options {text}")
        prompt = (
            f"Rows of a spreadsheet are imported as {Model._description} [{Model._name}] records in Odoo, the business "
            "software. Some values match no record or option: for each, choose the option it means (same meaning, "
            "even if written differently: \"15%\" is a tax of 15%), else create it when records can be created and "
            "the value is a real name (the request may ask to create new values), else leave it empty. Never match "
            "two different values with one option, nor a code or number with an option that does not hold it: "
            "\"1000- Aripero\" and \"1002- Carenage\" are two accounts, not \"Bank\". For each "
            "required field the file lacks, choose the option that fits the request and the file, or give a value "
            "(null when none fits).\n"
            "Reply with ONLY minified JSON, no text: {\"values\":{\"column_N\":{\"<value>\":{\"match\":<option id or "
            "key>}|{\"create\":true}|{\"empty\":true}}},\"new\":{\"column_N\":true|false},\"defaults\":"
            "{\"default_<field>\":<option id or key or value>|null}}\n"
            f"Request: {question}\nColumns of the file: {' | '.join(headers)}\n\n" + "\n\n".join(parts)
        )
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage)) or {}
        except UserError as error:
            _logger.info("AI Chat Pro: the values of a file could not be repaired by the AI: %s", error)
            answer = {}
        return answer if isinstance(answer, dict) else {}

    @api.model
    def _get_coded_names(self, field, values, descriptions=None):
        """ The names new records are created with, from values made of a code: the code
        first, written with letters, digits and dots only, and unique among the records
        that hold codes ("1000- Aripero" and "1000- Farah St": 1000 Aripero, 1000.1 Farah
        St). """
        Comodel = self.env[field.comodel_name]
        has_code = 'code' in Comodel._fields
        parts = {value: (re.sub(r'[^\w.]', '', _get_code(value)).strip('.'), _get_code_rest(value)) for value in values}
        taken = set()
        if has_code:
            codes = list({code for code, _rest in parts.values() if code})
            try:
                taken = set(Comodel.search([('code', 'in', codes)]).mapped('code')) if codes else set()
            except (AccessError, UserError, ValueError):
                taken = set()
        names = {}
        for value, (code, rest) in parts.items():
            if not has_code or not code:
                names[value] = value
                continue
            unique, suffix = code, 0
            while unique in taken:
                suffix += 1
                unique = f"{code}.{suffix}"
            taken.add(unique)
            # a value made of a code alone is named by its row ("1000" | "Leasehold Improvements")
            names[value] = f"{unique} {rest or (descriptions or {}).get(value) or code}"
        return names

    @api.model
    def _apply_repair(self, field, value, candidates, may_create, decision, Model=None):
        """ The value written instead of a value the import can not read, how it is
        shown to the user, and the values of the record to create, if any.

        :return: ``(value written, fix shown, values of the record to create or None)``
        """
        label = field._description_string(self.env)
        match = decision.get('match')
        option = next((c for c in candidates if match is not None and str(c.get('id', c.get('key'))) == str(match)), None)
        if option:
            return str(option.get('id', option.get('key'))), {'kind': 'match', 'text': self.env._(
                "%(field)s: \"%(value)s\" read as %(option)s.", field=label, value=value, option=option['name'],
            )}, None
        create = decision.get('create')
        if create and may_create:
            values = self._get_create_values(field, value, may_create, create)
            if values is not None:
                details = ", ".join(f"{v}" for k, v in values.items() if k != 'name' and v not in (None, ''))
                return CREATE_TOKEN + value, {'kind': 'create', 'text': self.env._(
                    "%(field)s: \"%(value)s\" does not exist and will be created%(details)s.",
                    field=label, value=values.get('name') or value, details=f" ({details})" if details else "",
                )}, values
        if field.required and Model is not None and field.type == 'many2one':
            # a required link is left to its default rather than failing the row
            default = Model.default_get([field.name]).get(field.name)
            if default:
                record = self.env[field.comodel_name].browse(default)
                return str(record.id), {'kind': 'match', 'text': self.env._(
                    "%(field)s: \"%(value)s\" matches no record: set to the default, %(default)s.",
                    field=label, value=value, default=record.display_name,
                )}, None
        return '', {'kind': 'empty', 'text': self.env._(
            "%(field)s: \"%(value)s\" matches no record and was left empty.", field=label, value=value,
        ) if field.relational else self.env._(
            "%(field)s: \"%(value)s\" is no valid option and was left empty.", field=label, value=value,
        )}, None

    @api.model
    def _get_create_values(self, field, value, spec, create):
        """ The values of a record to create for a value of a file, checked against what
        the AI may give; ``None`` when they are not enough. """
        if spec['mode'] == 'name':
            return {'name': create.get('name') if isinstance(create, dict) and create.get('name') else value}
        if not isinstance(create, dict):
            return None
        Comodel = self.env[field.comodel_name]
        values = {Comodel._rec_name: str(create.get('name') or create.get(Comodel._rec_name) or value).strip()[:200]}
        for name, (_label, kind, options) in spec['fields'].items():
            raw = create.get(name)
            if raw in (None, ''):
                continue
            if options is not None:
                if str(raw) not in options:
                    continue
                values[name] = str(raw)
            elif kind in ('integer', 'float', 'monetary'):
                number = _parse_number(str(raw))
                if number is not None:
                    values[name] = int(number) if kind == 'integer' else number
            elif kind == 'boolean':
                values[name] = str(raw).lower() in TRUE_WORDS
            elif kind == 'date':
                parsed = _parse_date(str(raw))
                if parsed:
                    values[name] = parsed.strftime('%Y-%m-%d')
            else:
                values[name] = str(raw).strip()[:200]
        required = [name for name in spec['fields'] if name not in CREATE_EXTRA_FIELDS]
        return values if all(name in values for name in required) else None

    @api.model
    def _check_matches(self, field, pending, answers):
        """ The decisions of the AI, without the matches merging values that are not
        the same: two different codes ("1000- Aripero", "1002- Carenage") matched with
        one record, or a code matched with a record not holding it. """
        by_option = {}
        for value, decision in answers.items():
            if isinstance(decision, dict) and decision.get('match') is not None:
                by_option.setdefault(str(decision['match']), []).append(value)
        rejected = set()
        for option, values in by_option.items():
            candidates = next((pending[v] for v in values if v in pending), [])
            name = next((c['name'] for c in candidates if str(c.get('id', c.get('key'))) == option), '')
            numbers = {tuple(re.findall(r'\d{3,}', value)) for value in values}
            if len(values) > 1 and len(numbers) > 1:
                rejected.update(values)
            for value in values:
                if any(number not in name for number in re.findall(r'\d{3,}', value)):
                    rejected.add(value)
        checked = dict(answers)
        for value in rejected:
            decision = dict(checked[value])
            decision.pop('match', None)
            # a value not matched is created when the AI also said how
            checked[value] = decision if decision.get('create') else {'create': True, 'rejected_match': True}
        return checked

    # ------------------------------------------------------------
    # Test imports and import
    # ------------------------------------------------------------

    @api.model
    def _run_import_plan(self, model_name, plan, context, dryrun):
        """ Import the rows of a plan, leaving out the rows that fail, until none does:
        records to create from a name are created first. With ``dryrun``, nothing is
        kept.

        :return: ``(ids of the records imported, plan updated with the rows left out)``
        """
        plan = dict(plan, rows=[list(row) for row in plan['rows']], row_numbers=list(plan['row_numbers']),
                    skipped=list(plan.get('skipped') or []), blocking=[])
        ids = []
        for _round in range(MAX_REPAIR_ROUNDS):
            if not plan['rows']:
                break
            savepoint = self.env.cr.savepoint()
            failed = []
            try:
                created = self._create_planned_records(model_name, plan['creates'], failed)
                content = _write_csv(plan['paths'], [_resolve_tokens(row, plan['paths'], created) for row in plan['rows']])
                importer = self.env['base_import.import'].create({
                    'res_model': model_name, 'file': content, 'file_name': 'import.csv', 'file_type': 'text/csv',
                })
                result = importer.with_context(**(context or {})).execute_import(
                    plan['paths'], plan['paths'], dict(CLEAN_OPTIONS), dryrun=dryrun,
                )
            except Exception:
                savepoint.close(rollback=True)
                self.env.invalidate_all()
                raise
            errors = [message for message in result.get('messages') or [] if message.get('type') == 'error']
            if failed:
                # said once: the values are left empty from now on
                plan['fixes'].extend({'kind': 'empty', 'text': text} for text in failed)
                plan['creates'] = {path: [r for r in records if created.get((path, r['value'])) != '']
                                   for path, records in plan['creates'].items()}
                for row in plan['rows']:
                    for position, path in enumerate(plan['paths']):
                        if CREATE_TOKEN in row[position]:
                            row[position] = ','.join(filter(None, (
                                '' if part.startswith(CREATE_TOKEN) and created.get((path, part.removeprefix(CREATE_TOKEN))) == ''
                                else part for part in row[position].split(','))))
            if not errors and (dryrun or result.get('ids')):
                ids = result.get('ids') or []
                savepoint.close(rollback=dryrun)
                if dryrun:
                    self.env.invalidate_all()
                break
            savepoint.close(rollback=True)
            self.env.invalidate_all()
            if not self._leave_out_failing_rows(plan, errors):
                typed = [record for records in plan['creates'].values() for record in records if record.get('set')]
                if typed:
                    # the types the AI gave the new records may be what blocks: Odoo's own types instead
                    for record in typed:
                        record.pop('set')
                    plan['fixes'].append({'kind': 'empty', 'text': self.env._(
                        "The types given to the new records blocked the import: they keep the types Odoo gives them.")})
                    continue
                plan['blocking'] = list(dict.fromkeys(
                    re.sub(r'\s+', ' ', str(error.get('message') or '')).strip()[:300] for error in errors))[:5]
                break
        return ids, plan

    @api.model
    def _create_planned_records(self, model_name, creates, failed=None):
        """ Create the records the plan creates from their name: ``{(path, name): id}``,
        an empty id for those that could not be created (listed in ``failed``). """
        failed = failed if failed is not None else []
        created = {}
        for path, records in (creates or {}).items():
            field, _Model = self._get_import_field(model_name, path.removesuffix('/.id'))
            Comodel = self.env[field.comodel_name]
            for record in records:
                if (path, record['value']) in created:
                    continue
                values = record.get('values') or {}
                try:
                    with self.env.cr.savepoint():
                        if set(values) - {'name'}:
                            created[(path, record['value'])] = Comodel.create(values).id
                        else:
                            # as an import does: an account named "1000 Cash" gets the code 1000
                            created[(path, record['value'])] = Comodel.with_context(import_file=True).name_create(
                                values.get('name') or record['value'])[0]
                        if record.get('set'):
                            Comodel.browse(created[(path, record['value'])]).write(record['set'])
                except Exception as error:  # noqa: BLE001 - any error creating it: the value is left empty
                    _logger.info("AI Chat Pro: %r could not be created for an import: %s", record['value'], error)
                    created[(path, record['value'])] = ''
                    failed.append(self.env._(
                        "\"%(value)s\" could not be created and was left empty: %(error)s",
                        value=record['value'], error=str(error.args[0] if error.args else error)[:150],
                    ))
        return created

    @api.model
    def _get_incomplete_lines(self, plan):
        """ The lines of a plan with a link left empty while the line has other values:
        ``{row index: reason}``. """
        links = [position for position, path in enumerate(plan['paths'])
                 if path.endswith('/.id') and path.startswith(f"{plan['lines_field']}/")]
        incomplete = {}
        for index, row in enumerate(plan['rows']):
            empty = [position for position in links if not row[position]]
            filled = [cell for position, cell in enumerate(row) if cell and position not in links]
            if empty and filled:
                labels = ", ".join(plan['paths'][position].split('/')[-2] for position in empty)
                incomplete[index] = self.env._("the line has no %s (a total, or a value not found)", labels)
        return incomplete

    @api.model
    def _leave_out_failing_rows(self, plan, errors):
        """ Leave out of a plan the rows the errors of a test import name, or the column
        an error names without rows. Whether anything was left out. """
        failing = {}
        lines = plan.get('lines_field')
        for error in errors:
            rows = error.get('rows') or {}
            text = re.sub(r'\s+', ' ', str(error.get('message') or '')).strip()[:200]
            if lines and isinstance(rows.get('from'), int) and rows.get('to', rows['from']) > rows['from']:
                # an error of the record of the lines names all its rows: the lines lacking a link
                # (a total, a blank line, an account not found) fail it, the others are kept
                culprits = self._get_incomplete_lines(plan)
                if not culprits:
                    return False
                failing.update({index: reason for index, reason in culprits.items() if index not in failing})
                continue
            if isinstance(rows.get('from'), int):
                for index in range(rows['from'], (rows.get('to') if isinstance(rows.get('to'), int) else rows['from']) + 1):
                    failing.setdefault(index, text)
            elif error.get('field_path') and '/'.join(error['field_path']) in plan['paths']:
                position = plan['paths'].index('/'.join(error['field_path']))
                plan['paths'].pop(position)
                for row in plan['rows']:
                    row.pop(position)
                plan['fixes'].append({'kind': 'empty', 'text': self.env._(
                    "A column was left out, as its values can not be read: %s", text)})
                return True
        failing = {index: text for index, text in failing.items() if index < len(plan['rows'])}
        if not failing:
            return False
        for index in sorted(failing, reverse=True):
            plan['skipped'].append({'row': plan['row_numbers'][index], 'reason': failing[index]})
            row = plan['rows'].pop(index)
            plan['row_numbers'].pop(index)
            if lines and index == 0 and plan['rows']:
                # the values of the record of the lines move to its new first row
                plan['rows'][0] = [new or old for new, old in zip(plan['rows'][0], row)]
        plan['skipped'].sort(key=lambda skip: skip['row'])
        return True


def _get_code(value):
    """ The code a value starts with: "1000" in "1000- Aripero"; empty if none. """
    match = CODE_RE.match(value or '')
    return match.group(1).strip() if match and any(char.isdigit() for char in match.group(1)) else ''


def _get_code_rest(value):
    match = CODE_RE.match(value or '')
    return match.group(2).strip(' -–:') if match else value


def _get_position(key):
    try:
        return int(str(key).removeprefix('column_'))
    except ValueError:
        return None


def _to_cell(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return '' if value is None or value is False else str(value)


def _parse_number(value):
    """ A number written in any common way: "1,234.50", "1.234,50", "₹ 1,200", "(50)",
    "15%". ``None`` when it is none. """
    text = NUMBER_RE.sub('', value.replace(' ', '').replace(' ', ''))
    negative = text.startswith('(') and text.endswith(')') or text.startswith('-')
    text = text.strip('()-')
    if not text or not any(char.isdigit() for char in text):
        return None
    if ',' in text and '.' in text:
        decimal = ',' if text.rfind(',') > text.rfind('.') else '.'
        text = text.replace('.' if decimal == ',' else ',', '').replace(',', '.')
    elif ',' in text:
        # "1,234" is a thousand, "12,5" a decimal number
        head, _sep, tail = text.rpartition(',')
        text = text.replace(',', '') if len(tail) == 3 and head.replace(',', '').isdigit() else text.replace(',', '.')
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _parse_date(value):
    try:
        return date_parser.parse(value, dayfirst=True) if re.match(r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}', value) \
            else date_parser.parse(value)
    except (ValueError, OverflowError):
        return None


def _replace_value(cell, value, replacement, field):
    if field.type == 'many2many':
        names = [name.strip() for name in cell.split(',')] if cell else []
        return ','.join(filter(None, (replacement if name == value else name for name in names)))
    return replacement if cell == value else cell


def _resolve_tokens(row, paths, created):
    """ A row, the names of records created replaced by their ids (empty for those that
    could not be created). """
    resolved = []
    for path, cell in zip(paths, row):
        if CREATE_TOKEN in cell:
            cell = ','.join(filter(None, (
                str(created.get((path, part.removeprefix(CREATE_TOKEN))) or '') if part.startswith(CREATE_TOKEN) else part
                for part in cell.split(',')
            )))
        resolved.append(cell)
    return resolved


def _write_csv(header, rows):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')

