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

import base64
import json
import logging
import re
from datetime import date, datetime

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.safe_eval import safe_eval

from .ai_chat_assistant import _keywords, _stem, _words
from .ai_chat_creator import _loads_loosely
from .ai_chat_document import get_document_type

_logger = logging.getLogger(__name__)

# the files a question can come with: spreadsheets, read by the import of Odoo
SPREADSHEET_TYPES = {
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet',
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS = 3
# rows of a file read: imported at most, shown in the draft, given to the AI to answer about it
MAX_IMPORT_ROWS = 5000
MAX_SHOWN_ROWS = 5
MAX_ANSWER_ROWS = 60
MAX_SHOWN_ERRORS = 8
MAX_SHOWN_FIXES = 30
# fields offered to the AI to map the columns Odoo did not match
MAX_MAPPING_FIELDS = 80
# the keys of a menu's context that set the records it creates (customers: res_partner_search_mode)
CONTEXT_KEYS_RE = re.compile(r'^(?:default_\w+|\w+_search_mode|journal_type|move_type)$')
DEFAULT_IMPORT_OPTIONS = {
    'encoding': '', 'separator': '', 'quoting': '"', 'date_format': '', 'datetime_format': '',
    'float_thousand_separator': ',', 'float_decimal_separator': '.', 'advanced': True, 'has_headers': True,
    'keep_matches': False, 'limit': MAX_IMPORT_ROWS, 'sheets': [], 'sheet': '', 'skip': 0,
    'tracking_disable': True, 'import_skip_records': [], 'import_set_empty_fields': [], 'fallback_values': {},
    'name_create_enabled_fields': {},
}


def get_spreadsheet_type(name):
    """ The mimetype of a spreadsheet, from its file name; ``None`` for other files. """
    return SPREADSHEET_TYPES.get((name or '').rpartition('.')[2].lower())


class AiChatAssistant(models.AbstractModel):
    """ Questions asked with a spreadsheet: "create customers from the attached file"
    imports its rows as records of any model, with the import of Odoo (as the user,
    after confirming a draft showing how its columns are read); other questions are
    answered from its rows. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _answer_with_attachment(self, question, attachments, usage, creates=False):
        """ The file tool of the agent: a request to create records from a file sent with
        the question imports it, other questions are answered from it.

        :param bool creates: whether the request asks to create records from the file, as
            the agent read it
        """
        attachment = attachments[0]
        if creates and not self._is_create_enabled():
            raise UserError(self.env._("Creating records from the chat is disabled in the settings."))
        if get_document_type(attachment.name):
            # a document (an invoice, an order): one record is drafted from its text
            return self._draft_from_document(question, attachment, usage) if creates \
                else self._answer_about_document(question, attachment, usage)
        if not get_spreadsheet_type(attachment.name):
            raise UserError(self.env._("\"%s\" can not be read: send a spreadsheet, a PDF or a picture.", attachment.name))
        if creates:
            return self._draft_import(question, attachment, usage)
        return self._answer_about_file(question, attachment, usage)

    # ------------------------------------------------------------
    # Import
    # ------------------------------------------------------------

    @api.model
    def _choose_import_model(self, question, usage):
        """ The kind of records a request asks to import, as the agent read it:
        "customers" in "create customers based on the attached file". """
        target = self._get_intent().get('target') or ''
        if _keywords(target):
            return self._choose_create_model(question, target, usage)
        return None

    @api.model
    def _get_import_context(self, candidate):
        """ The defaults of the menu the records are matched on: Sales > Customers makes
        its contacts customers, Invoicing > Bills makes its moves vendor bills. """
        context = candidate.get('context') or {}
        if isinstance(context, str):
            try:
                context = safe_eval(context, self._get_eval_context())
            except Exception:  # noqa: BLE001 - a context needing the web client's values
                context = {}
        return {key: value for key, value in (context or {}).items()
                if CONTEXT_KEYS_RE.match(key) and isinstance(value, (str, int, float, bool))}

    @api.model
    def _new_import(self, model_name, attachment):
        attachment.check_access('read')
        return self.env['base_import.import'].create({
            'res_model': model_name,
            'file': attachment.raw,
            'file_name': attachment.name,
            'file_type': get_spreadsheet_type(attachment.name),
        })

    @api.model
    def _draft_import(self, question, attachment, usage):
        """ The draft of the import of a spreadsheet, repaired so that it is not blocked:
        how its columns are read, what was changed in its values, the rows left out and
        why, and its first rows, for the user to confirm. """
        headers, rows = self._read_import_rows(attachment)
        if not rows:
            raise UserError(self.env._("The file has no rows to import: its first line must name the columns."))
        if len(rows) > MAX_IMPORT_ROWS:
            raise UserError(self.env._(
                "The file has %(count)s rows: import at most %(max)s at a time.", count=len(rows), max=MAX_IMPORT_ROWS,
            ))
        candidate, lines_field = self._choose_import_target(question, headers, rows, usage)
        if not candidate:
            return {'content': self.env._(
                "Which kind of records does the file hold? Say it, e.g. \"create customers from the attached file\" "
                "or \"import these products\".",
            ), 'is_error': True}
        model_name, label = candidate['model'], candidate['label']
        importer = self._new_import(model_name, attachment)
        preview = importer.parse_preview(dict(DEFAULT_IMPORT_OPTIONS), count=MAX_SHOWN_ROWS + 1)
        if preview.get('error'):
            raise UserError(self.env._("The file could not be read: %s", preview['error']))
        fields_tree = preview['fields']
        matches = {int(index): path for index, path in (preview.get('matches') or {}).items()}
        one2many = {field['name'] for field in fields_tree if field['type'] == 'one2many'}
        # a column matched with the lines of a record itself holds none of them
        matches = {index: path for index, path in matches.items() if not (len(path) == 1 and path[0] in one2many)}
        if lines_field:
            # the rows are lines: only the columns of the record itself stay matched by Odoo
            matches = {index: path for index, path in matches.items() if path[0] != lines_field}
        mapped_by = {index: 'odoo' for index in matches}
        # required fields are never left to the AI: a column naming one ("Customer Name") holds it
        for index, path in self._map_required_columns(model_name, headers, matches, fields_tree).items():
            if not lines_field:
                matches[index] = path
                mapped_by[index] = 'name'
        unmatched = [index for index in range(len(headers)) if index not in matches]
        if unmatched:
            for index, path in self._map_columns_by_ai(
                model_name, headers, preview['preview'], unmatched, fields_tree, set(map(tuple, matches.values())),
                usage, lines_field=lines_field,
            ).items():
                matches[index] = path
                mapped_by[index] = 'ai'
        import_fields, used = [], set()
        for index in range(len(headers)):
            path = matches.get(index)
            # a field is read from one column only
            if path and tuple(path) not in used:
                used.add(tuple(path))
                import_fields.append('/'.join(path))
            else:
                import_fields.append(False)
        if not any(import_fields):
            raise UserError(self.env._(
                "No column of the file matches a field of %s: name the columns like the fields, e.g. \"Name\", "
                "\"Email\".", label,
            ))
        if lines_field and not any(name and name.startswith(f"{lines_field}/") for name in import_fields):
            # no column fills the lines: each row is a record after all
            lines_field = False
        context = self._get_import_context(candidate)
        # the file name may say what the rows do not ("Trial balance as at 31.12.2025")
        plan = self._repair_import(f"{question}\n(File: \"{attachment.name}\")", model_name, headers, rows,
                                   import_fields, context, usage, lines_field)
        # test imports, rolled back: the rows that still fail are left out, with their reason
        _ids, plan = self._run_import_plan(model_name, plan, context, dryrun=True)
        plan_file = self.env['ir.attachment'].create({
            'name': f"{attachment.name}.import.json", 'mimetype': 'application/json',
            'raw': json.dumps(plan).encode(),
        })
        labels = _get_field_labels(fields_tree)
        shown = [index for index, name in enumerate(import_fields) if name]
        kept = [number - 2 for number in plan['row_numbers'][:MAX_SHOWN_ROWS]]
        count = len(plan['rows'])
        draft = {
            'type': 'import',
            'state': 'draft',
            'model': model_name,
            'model_label': label,
            'title': self.env._("Import %(count)s %(label)s records", count=count, label=label) if not lines_field
            else self.env._("Import 1 %(label)s with %(count)s lines", count=count, label=label),
            'file_name': attachment.name,
            'attachment_id': attachment.id,
            'plan_attachment_id': plan_file.id,
            'count': count,
            'total': len(rows),
            'lines_field': lines_field,
            'mapping': [{
                'column': header,
                'field': labels.get(import_fields[index]) or import_fields[index] if import_fields[index] else False,
                'by': mapped_by.get(index) if import_fields[index] else False,
            } for index, header in enumerate(headers)],
            'columns': [labels.get(import_fields[index]) or import_fields[index] for index in shown],
            'rows': [[_to_text(rows[row][index]) if index < len(rows[row]) else '' for index in shown] for row in kept],
            'fixes': plan['fixes'][:MAX_SHOWN_FIXES],
            'fix_count': len(plan['fixes']),
            'skipped': plan['skipped'][:MAX_SHOWN_ERRORS],
            'skipped_count': len(plan['skipped']),
            # what blocks the whole import, that no row or column explains (an entry not balanced)
            'errors': plan.get('blocking') or [], 'error_count': len(plan.get('blocking') or []),
            'context': context,
        }
        ignored = [header for header, name in zip(headers, import_fields) if not name]
        content = self.env._("I read %(total)s rows of \"%(file)s\" as %(label)s.",
                             total=len(rows), file=attachment.name, label=label)
        if plan['fixes']:
            content += " " + self.env._("I repaired %s problems of the values, listed below.", len(plan['fixes']))
        if plan['skipped']:
            content += " " + self.env._("%s rows still fail and will be left out, with their reason.", len(plan['skipped']))
        if plan.get('blocking'):
            content += " " + self.env._("The import is still blocked: %s", plan['blocking'][0])
        else:
            content += " " + (self.env._("Check it, then import the %s rows.", count) if count
                              else self.env._("No row can be imported."))
        if ignored:
            content += " " + self.env._("Columns ignored: %s.", ", ".join(ignored))
        source = 'openrouter_olg' if usage['ai_called'] else 'olg'
        return {'content': content, 'result': draft, 'source': source}

    @api.model
    def _map_required_columns(self, model_name, headers, matches, fields_tree):
        """ The columns Odoo did not match whose name holds the label of a required field,
        or of the name of the records, not matched yet: "Customer Name" for the name of a
        contact (required by a constraint, not by its field).

        :return: ``{column index: field path}``
        """
        taken = {path[0] for path in matches.values()}
        rec_name = self.env[model_name]._rec_name
        result = {}
        # the name of the records first: "Customer Name" names a contact before its company
        for field in sorted(fields_tree, key=lambda field: field['name'] != rec_name):
            if (not field.get('required') and field['name'] != rec_name) or field['name'] in taken \
                    or field['name'] in ('id', '.id'):
                continue
            label_words = [_stem(word) for word in _words(field['string'])]
            for index, header in enumerate(headers):
                header_words = [_stem(word) for word in _words(header)]
                if index in matches or index in result or not label_words:
                    continue
                # the label, as the last words of the column's name
                if header_words[-len(label_words):] == label_words:
                    result[index] = [field['name']]
                    break
        return result

    @api.model
    def _map_columns_by_ai(self, model_name, headers, examples, columns, fields_tree, taken, usage, lines_field=False):
        """ The fields of the columns Odoo did not match, read by the AI from their names
        and first values; columns it does not match are ignored. When the rows are the
        lines of one record, the fields of its lines are offered first.

        :return: ``{column index: field path}``
        """
        Model = self.env[model_name]
        create_fields = self._get_create_fields(Model)
        form_fields = list(create_fields)
        # a column holds a value, never the lines of a record (a column of debits is no journal items)
        offered = [field for field in fields_tree if field['name'] not in ('id', '.id', lines_field)
                   and field['type'] != 'one2many' and (field['name'],) not in taken]
        # the fields of the form first: the ones users fill
        offered.sort(key=lambda field: (not field['required'], field['name'] not in form_fields))
        if lines_field:
            lines = next((field for field in fields_tree if field['name'] == lines_field), None)
            line_form = create_fields.get(lines_field) or []
            sub_fields = sorted(
                (field for field in (lines or {}).get('fields') or [] if field['name'] not in ('id', '.id')),
                key=lambda field: (field['name'] not in line_form, not field['required']),
            )
            offered = [dict(field, name=f"{lines_field}/{field['name']}",
                            string=f"{lines['string']} / {field['string']}") for field in sub_fields] + offered
        offered = offered[:MAX_MAPPING_FIELDS]
        described = "\n".join(
            f"- {field['name']} ({field['string']}, {field['type']}"
            + (", by name" if field['type'] in ('many2one', 'many2many') else "")
            + (", required" if field['required'] else "") + ")"
            for field in offered
        )
        columns_text = "\n".join(
            f"- {headers[index]!r}: e.g. {', '.join(repr(value) for value in (examples[index] or [])[:3])}"
            for index in columns
        )
        prompt = (
            f"Columns of a spreadsheet are imported as records of {Model._description} [{model_name}] in Odoo. Match "
            "each column below with the field it holds, from its name and values, or null when no field fits. A "
            "field is matched with one column at most.\n"
            "Reply with ONLY minified JSON, no text: {\"mapping\":{\"<column>\":\"<field name>\"|null}}\n"
            f"Columns:\n{columns_text}\nFields:\n{described}"
        )
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage)) or {}
        except UserError as error:
            _logger.info("AI Chat Pro: the columns of a file could not be matched by the AI: %s", error)
            return {}
        mapping = answer.get('mapping') if isinstance(answer, dict) else None
        names = {field['name'] for field in offered}
        result, used = {}, set()
        for index in columns:
            name = (mapping or {}).get(headers[index]) if isinstance(mapping, dict) else None
            if isinstance(name, str) and name in names and name not in used:
                used.add(name)
                result[index] = name.split('/')
        return result

    @api.model
    def _import_from_draft(self, draft):
        """ Import the rows of the repaired plan of a draft, as the current user: rows
        failing now are left out too, the others are imported.

        :return: ``(ids of the records created, rows left out)``
        """
        if not self._can_create(draft['model']):
            raise AccessError(self.env._("You are not allowed to create %s records.", draft['model_label']))
        plan_file = self.env['ir.attachment'].browse(draft.get('plan_attachment_id')).exists()
        if not plan_file:
            raise UserError(self.env._("The file of this import no longer exists: send it again."))
        plan = json.loads(bytes(plan_file.raw) or b'{}')
        ids, plan = self._run_import_plan(draft['model'], plan, draft.get('context') or {}, dryrun=False)
        if not ids:
            reasons = "; ".join(plan.get('blocking') or []) or "; ".join(
                f"row {skip['row']}: {skip['reason']}" for skip in plan['skipped'][:3])
            raise UserError(self.env._("No row could be imported: %s", reasons or self.env._("no row to import")))
        return ids, plan['skipped']

    # ------------------------------------------------------------
    # Questions on a file
    # ------------------------------------------------------------

    @api.model
    def _answer_about_file(self, question, attachment, usage):
        """ Answer a question on the rows of a spreadsheet, by the AI writing answers. """
        importer = self._new_import('res.partner', attachment)
        options = dict(DEFAULT_IMPORT_OPTIONS)
        try:
            length, rows = importer._read_file(options)
            rows = list(rows)
        except Exception as error:  # noqa: BLE001 - any error of the file's reader
            raise UserError(self.env._("The file could not be read: %s", error))
        shown = rows[:MAX_ANSWER_ROWS + 1]
        more = (f" (the first {MAX_ANSWER_ROWS} of {len(rows) - 1} rows)" if len(rows) - 1 > MAX_ANSWER_ROWS else "")
        data = "\n".join(" | ".join(_to_text(cell)[:60] for cell in row) for row in shown)
        prompt = (
            "Answer the question of a user on the spreadsheet they sent, using only its rows below. Be concise: at "
            "most 150 words, plain text. Say so when the rows do not answer the question.\n"
            f"Question: {question}\nFile \"{attachment.name}\"{more}, first row naming the columns:\n{data}"
        )
        answer = self._text_chat(prompt, usage)
        source = 'openrouter_olg' if usage['ai_called'] else 'olg'
        return {'content': answer.strip(), 'source': source}


def _get_field_labels(fields_tree, prefix='', label_prefix=''):
    """ The labels of the fields an import can fill, by path: "Country" for
    country_id, "Tags / External ID" for category_id/id. """
    labels = {}
    for field in fields_tree:
        path = f"{prefix}{field['name']}"
        label = f"{label_prefix}{field['string']}"
        labels[path] = label
        if field.get('fields') and not prefix:
            labels.update(_get_field_labels(field['fields'], f"{path}/", f"{label} / "))
    return labels


def _to_text(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return '' if value is None or value is False else str(value)


class AiChatConversation(models.Model):
    _inherit = 'ai.chat.conversation'

    @api.model
    def upload_chat_attachment(self, name, data):
        """ Store a file sent with a question, before the question is asked: only its
        sender can read it until then.

        :param str data: the file, in base64
        :return: ``{id, name, size}``
        """
        self._check_chat_access()
        name = (name or '').strip()[:200]
        mimetype = get_spreadsheet_type(name) or get_document_type(name)
        if not mimetype:
            raise UserError(self.env._(
                "Only spreadsheets (CSV, XLSX, XLS, ODS), PDFs and pictures (PNG, JPG, WEBP) can be sent."))
        try:
            raw = base64.b64decode(data or '', validate=True)
        except ValueError:
            raise UserError(self.env._("The file could not be read."))
        if not raw:
            raise UserError(self.env._("The file is empty."))
        if len(raw) > MAX_ATTACHMENT_SIZE:
            raise UserError(self.env._("The file is too large: send files of 10 MB at most."))
        attachment = self.env['ir.attachment'].create({'name': name, 'raw': raw, 'mimetype': mimetype})
        return {'id': attachment.id, 'name': attachment.name, 'size': attachment.file_size, 'mimetype': mimetype}

    @api.model
    def _get_question_attachments(self, attachment_ids):
        """ The files sent with a question: sent by the current user, not asked with
        another question yet. """
        if not attachment_ids:
            return self.env['ir.attachment']
        if len(attachment_ids) > MAX_ATTACHMENTS:
            raise UserError(self.env._("Send %s files at most with a question.", MAX_ATTACHMENTS))
        attachments = self.env['ir.attachment'].browse(attachment_ids).exists()
        if len(attachments) != len(set(attachment_ids)) or any(
                attachment.create_uid != self.env.user or attachment.res_model for attachment in attachments.sudo()):
            raise AccessError(self.env._("These files can not be sent with this question."))
        return attachments

    @api.model
    def get_import_records_action(self, message_id):
        """ The list of the records an import of the current user created. """
        message = self._get_draft_message(message_id)
        result = message.result
        if result.get('type') != 'import' or result.get('state') != 'created':
            raise UserError(self.env._("This import created no record."))
        return {
            'type': 'ir.actions.act_window',
            'name': result['title'],
            'res_model': result['model'],
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', result.get('res_ids') or [])],
            'target': 'current',
        }

    def _import_draft_values(self, message, result):
        """ Import the rows of an import draft, and the values of the answer once done. """
        ids, skipped = self.env['ai.chat.assistant']._import_from_draft(result)
        result.update(state='created', res_ids=ids, created=len(ids),
                      skipped=skipped[:MAX_SHOWN_ERRORS], skipped_count=len(skipped))
        content = self.env._("%(count)s %(label)s records created from \"%(file)s\".",
                             count=len(ids), label=result['model_label'], file=result['file_name'])
        if skipped:
            content += " " + self.env._("%s rows were left out, as they still fail.", len(skipped))
        return result, content


class AiChatMessage(models.Model):
    _inherit = 'ai.chat.message'

    attachment_ids = fields.Many2many(
        'ir.attachment', 'ai_chat_message_attachment_rel', 'message_id', 'attachment_id', string="Files",
    )

    def _get_chat_values(self):
        values = super()._get_chat_values()
        values['attachments'] = [
            {'id': attachment.id, 'name': attachment.name, 'size': attachment.file_size, 'mimetype': attachment.mimetype}
            for attachment in self.attachment_ids
        ]
        return values
