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

import difflib
import logging
import re

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import html2plaintext
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)

# the commands typed after "/" in the chat: what they do, and whether they need a record mentioned with "@"
COMMANDS = {
    'explain': {
        'description': "A detailed summary of a record, with its history and activities",
        'example': "/explain @…",
    },
    'report': {
        'description': "Print the Odoo report of a record, as a PDF",
        'example': "/report @…",
    },
}
COMMAND_RE = re.compile(r'(?:^|\s)/(?P<name>[a-z_]+)\b', re.IGNORECASE)
# what /explain reads of a record: its fields, its lines, its chatter and its activities
MAX_EXPLAIN_FIELDS = 45
MAX_EXPLAIN_LINES = 20
MAX_LINE_COLUMNS = 7
MAX_EXPLAIN_MESSAGES = 25
MAX_DONE_ACTIVITIES = 10
MAX_SHOWN_HISTORY = 8
MAX_EXPLAIN_TEXT = 9000
MAX_VALUE_TEXT = 300
# the reports /report prints: those of the Print menu of a record
REPORT_TYPES = ('qweb-pdf', 'qweb-html')
MAX_OTHER_REPORTS = 6


class AiChatConversation(models.Model):
    _inherit = 'ai.chat.conversation'

    @api.model
    def get_chat_data(self, conversation_id=False):
        data = super().get_chat_data(conversation_id)
        data['commands'] = [{'name': name, **command} for name, command in COMMANDS.items()]
        return data


class AiChatAssistant(models.AbstractModel):
    """ Commands typed after "/" in a question. ``/explain @S00100`` explains a record:
    the AI writes a detailed summary from its fields, its lines, its chatter and its
    activities, read as the user; the activities and the history are shown as Odoo
    holds them. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _answer_command(self, question, usage):
        """ The answer to a command typed after "/" (explicit syntax: no AI is needed to
        read it), or ``None`` when the question holds no command. """
        match = COMMAND_RE.search(question or '')
        if not match:
            return None
        name = match.group('name').lower()
        if name in COMMANDS:
            rest = (question[:match.start()] + ' ' + question[match.end():]).strip()
            return getattr(self, f'_command_{name}')(rest, usage)
        if question.strip().startswith('/'):
            return {'content': self.env._(
                "There is no command \"/%(name)s\". The commands are: %(commands)s.", name=name,
                commands=", ".join(f"/{command}" for command in COMMANDS),
            ), 'is_error': True}
        return None

    @api.model
    def _get_suggestions(self, question, values, usage):
        # a command says itself what it needs: no other question to offer
        match = COMMAND_RE.search(question or '')
        if match and (match.group('name').lower() in COMMANDS or question.strip().startswith('/')):
            return []
        return super()._get_suggestions(question, values, usage)

    # ------------------------------------------------------------
    # /explain
    # ------------------------------------------------------------

    @api.model
    def _get_command_record(self, rest):
        """ The record a command is about: the one mentioned with "@", else the one the
        text names plainly. """
        mentions = self._get_mentions()
        record = None
        if mentions:
            record = self.env[mentions[0]['model']].browse(mentions[0]['id']).exists()
        elif rest.strip():
            # a record named plainly ("the sales order S00042", "Azure Interior"): the one of the conversation,
            # else the one bearing exactly the name, else the only one that comes close
            for text in self._get_reference_texts(rest.strip()):
                if remembered := self._find_remembered_record({'label': '', 'text': text}):
                    record = self.env[remembered['model']].browse(remembered['id']).exists()
                    break
                found = self.env['ai.chat.conversation'].search_mentions(text)
                exact = [item for item in found if item['name'].strip().lower() == text.lower()]
                if exact or len(found) == 1:
                    item = (exact or found)[0]
                    record = self.env[item['model']].browse(item['id']).exists()
                    break
        if record:
            record.check_access('read')
        return record

    @api.model
    def _command_explain(self, rest, usage):
        """ Explain the record mentioned, else the one the text names. """
        record = self._get_command_record(rest)
        if not record:
            return {'content': self.env._(
                "Which record should I explain? Mention it with @ after the command.",
            ), 'is_error': True}
        data = self._get_record_data(record)
        explanation = self._write_explanation(record, data, usage)
        return {
            'content': explanation.get('overview') or self.env._("%(label)s %(name)s", label=record._description,
                                                                  name=record.display_name),
            'result': {
                'type': 'explain',
                'model': record._name,
                'id': record.id,
                'title': record.display_name,
                'model_label': record._description,
                **explanation,
                'activities': data['activities'],
                'history': data['history'][:MAX_SHOWN_HISTORY],
            },
        }

    @api.model
    def _get_record_data(self, record):
        """ What a record holds, as the user can read it: its fields, its lines, its
        chatter (messages and changes of tracked fields) and its activities. """
        Model = self.env[record._name]
        # the fields its form shows the user, else the stored ones
        names = self._get_form_fields(Model) or [name for name, field in Model._fields.items() if field.store]
        names = list(dict.fromkeys(
            [name for name in self._get_list_view_columns(Model) if name in Model._fields] + names
        ))
        values, lines = [], []
        for name in names:
            field = Model._fields[name]
            if field.type == 'binary' or not self._is_usable_field(Model, field) or not record[name]:
                continue
            if field.type == 'one2many':
                if len(lines) < 3:
                    lines.append(self._get_record_lines(record, field))
                continue
            if len(values) >= MAX_EXPLAIN_FIELDS:
                continue
            if field.type == 'html':
                value = html2plaintext(record[name] or '')
            elif field.type == 'many2many':
                value = ", ".join(record[name][:10].mapped('display_name'))
            else:
                value = self._format_field(record, field)
            value = re.sub(r'\s+', ' ', str(value)).strip()[:MAX_VALUE_TEXT]
            if value:
                values.append((field._description_string(self.env), value))
        return {
            'values': values,
            'lines': [table for table in lines if table['rows']],
            'history': self._get_record_history(record),
            'activities': self._get_record_activities(record),
        }

    @api.model
    def _get_form_arch(self, Model):
        try:
            return etree.fromstring(Model.get_views([(False, 'form')])['views']['form']['arch'])
        except Exception:  # noqa: BLE001 - models without a form view
            return None

    @api.model
    def _get_form_fields(self, Model):
        """ The fields of the form view of a model, as the user sees it, not those of its
        lines. """
        arch = self._get_form_arch(Model)
        if arch is None:
            return []
        names = []
        for node in arch.xpath('//field[not(ancestor::field)]'):
            name = node.get('name')
            if name in Model._fields and node.get('invisible') not in ('1', 'True') and name not in names:
                names.append(name)
        return names

    @api.model
    def _get_record_lines(self, record, field):
        Line = self.env[field.comodel_name]
        # the columns the form of the record shows its lines with, else those of their own list
        columns = []
        arch = self._get_form_arch(self.env[record._name])
        nodes = arch.xpath(f'//field[@name="{field.name}"][not(ancestor::field)]/list/field') if arch is not None else []
        for node in nodes:
            hidden = node.get('column_invisible') in ('1', 'True') or node.get('invisible') in ('1', 'True')
            if not hidden and node.get('optional') != 'hide' and node.get('widget') != 'handle' \
                    and node.get('name') in Line._fields:
                columns.append(node.get('name'))
        if not columns:
            try:
                columns = self._get_list_view_columns(Line)
            except Exception:  # noqa: BLE001 - lines without a list view
                columns = ['display_name']
        columns = [name for name in dict.fromkeys(columns) if name in Line._fields
                   and Line._fields[name].type not in ('one2many', 'many2many', 'binary', 'html')
                   and Line._fields[name].comodel_name != record._name
                   and self._is_usable_field(Line, Line._fields[name])][:MAX_LINE_COLUMNS] or ['display_name']
        rows = []
        for line in record[field.name][:MAX_EXPLAIN_LINES]:
            rows.append([re.sub(r'\s+', ' ', str(self._format_field(line, Line._fields[name]) or '')).strip()[:80]
                         for name in columns])
        return {
            'label': field._description_string(self.env),
            'columns': [Line._fields[name]._description_string(self.env) for name in columns],
            'rows': rows,
            'total': len(record[field.name]),
        }

    @api.model
    def _get_record_history(self, record):
        """ The chatter of a record, newest first: messages, notes and the changes of
        its tracked fields the user may read. """
        if 'message_ids' not in record._fields or record._fields['message_ids'].comodel_name != 'mail.message':
            return []
        history = []
        messages = record.message_ids.filtered(
            lambda m: m.message_type in ('comment', 'email', 'notification', 'tracking'))
        has_tracking_values = 'tracking_value_ids' in messages._fields  # the mail_tracking module is optional
        for message in messages.sorted('date', reverse=True)[:MAX_EXPLAIN_MESSAGES]:
            changes = [
                f"{change['fieldInfo']['changedField']}: {change['oldValue'] or '-'} → {change['newValue'] or '-'}"
                for change in message.sudo().tracking_value_ids._filter_has_field_access(self.env)._tracking_value_format()
            ] if has_tracking_values else []
            text = re.sub(r'\s+', ' ', html2plaintext(message.body or '')).strip()[:MAX_VALUE_TEXT]
            if not text and not changes:
                continue
            history.append({
                'date': fields.Datetime.to_string(message.date),
                'author': message.author_id.name or '',
                'kind': 'note' if message.subtype_id.internal else message.message_type,
                'text': text,
                'changes': changes,
            })
        return history

    @api.model
    def _get_record_activities(self, record):
        """ The activities of a record: planned ones (overdue, today, later), then the
        last ones done. """
        Activity = self.env['mail.activity']
        try:
            activities = Activity.with_context(active_test=False).search([
                ('res_model', '=', record._name), ('res_id', '=', record.id),
            ], order='active desc, date_deadline asc, id desc')
        except AccessError:
            return []
        planned = activities.filtered('active')
        done = activities.filtered(lambda a: not a.active)[:MAX_DONE_ACTIVITIES]
        return [{
            'type': activity.activity_type_id.name or '',
            'icon': activity.activity_type_id.icon or 'checklist',
            'summary': activity.summary or html2plaintext(activity.note or '').strip()[:120],
            'date': fields.Date.to_string(activity.date_deadline),
            'user': activity.user_id.name or '',
            'state': activity.state if activity.active else 'done',
        } for activity in planned + done]

    @api.model
    def _write_explanation(self, record, data, usage):
        """ The explanation the AI writes from the data of a record: ``{overview,
        key_points, history_summary, attention}``. """
        parts = [f"{label}: {value}" for label, value in data['values']]
        for table in data['lines']:
            more = f" (first {len(table['rows'])} of {table['total']})" if table['total'] > len(table['rows']) else ""
            parts.append(f"{table['label']}{more}: " + " | ".join(table['columns']) + "\n"
                         + "\n".join(" | ".join(row) for row in table['rows']))
        if data['activities']:
            parts.append("Activities:\n" + "\n".join(
                f"- {a['state']}: {a['type']} \"{a['summary']}\" due {a['date']}, for {a['user']}"
                for a in data['activities']))
        if data['history']:
            parts.append("Chatter, newest first:\n" + "\n".join(
                f"- {h['date']} {h['author']} ({h['kind']}): {h['text']}"
                + (f" [changes: {'; '.join(h['changes'])}]" if h['changes'] else "")
                for h in data['history']))
        text = "\n".join(parts)[:MAX_EXPLAIN_TEXT]
        today = fields.Date.context_today(self)
        answer = self._ask_json(
            f"Explain a record of Odoo, the business software, to its user, from its data below only: never invent a "
            f"fact. Today is {today}. Reply in English, with ONLY minified JSON, no text: {{\"overview\":\"<3 to 5 "
            "sentences: what this record is, its parties, amounts, state and where it stands>\",\"key_points\":[\"<a "
            "fact that matters, with its figures or dates; the main lines, if any>\"],\"history\":[\"<what happened, from the chatter, "
            "oldest first, with dates>\"],\"attention\":[\"<what needs attention or should be done next: overdue "
            "activities, missing values, risks>\"]}\nAt most 8 key points, 6 history items and 4 points of "
            "attention: only facts the data shows, each said once; a list may be empty rather than filled with vague "
            f"advice.\nRecord: {record._description} \"{record.display_name}\"\n{text}", usage,
        )
        if not answer:
            return {'overview': '', 'key_points': [], 'history_summary': [], 'attention': [],
                    'note': self.env._("The AI could not write the explanation: the data of the record is below.")}

        def texts(name, limit):
            items = answer.get(name)
            return [re.sub(r'\s+', ' ', str(item)).strip()[:400] for item in (items if isinstance(items, list) else [])
                    if str(item).strip()][:limit]
        return {
            'overview': re.sub(r'\s+', ' ', str(answer.get('overview') or '')).strip()[:1500],
            'key_points': texts('key_points', 8),
            'history_summary': texts('history', 6),
            'attention': texts('attention', 4),
        }

    # ------------------------------------------------------------
    # /report
    # ------------------------------------------------------------

    @api.model
    def _command_report(self, rest, usage):
        """ Print the report of the record mentioned: the first one of its Print menu (the
        default report of Odoo: the quotation of a sales order, the invoice of an
        invoice), or the one the text names ("/report @INV/2026/0001 without payment").
        A PDF when the server prints them, else the page of the report, to print from the
        browser. """
        record = self._get_command_record(rest)
        if not record:
            return {'content': self.env._(
                "Which record should I print? Mention it with @ after the command.",
            ), 'is_error': True}
        reports = self._get_record_reports(record)
        if not reports:
            return {'content': self.env._(
                "Odoo has no report to print for %(label)s %(name)s.", label=record._description,
                name=record.display_name,
            ), 'is_error': True}
        report = self._choose_record_report(reports, rest, record)
        pdf_engine = self.env['ai.chat.message']._has_pdf_engine()
        result = {
            'type': 'print',
            'model': record._name,
            'id': record.id,
            'title': record.display_name,
            'model_label': record._description,
            'report': {'id': report.id, 'name': report.name},
            'others': [{'id': other.id, 'name': other.name} for other in reports if other != report][:MAX_OTHER_REPORTS],
            'pdf_engine': pdf_engine,
        }
        if pdf_engine:
            file_name, content, _mimetype = self._render_record_report(report, record, pdf=True)
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name, 'raw': content, 'mimetype': 'application/pdf',
                'res_model': 'ai.chat.message', 'res_id': 0,
            })
            result.update({'attachment_id': attachment.id, 'file_name': file_name, 'file_size': len(content)})
            content_text = self.env._("%(report)s of %(name)s, printed as a PDF.", report=report.name,
                                      name=record.display_name)
        else:
            content_text = self.env._("%(report)s of %(name)s, ready to print: save it as a PDF from the print "
                                      "window.", report=report.name, name=record.display_name)
        return {'content': content_text, 'result': result}

    @api.model
    def _get_record_reports(self, record):
        """ The reports of the Print menu of a record the user may print, in the order of
        the menu: the first one is the default report. """
        reports = self.env['ir.actions.report'].sudo().search([
            ('model', '=', record._name), ('report_type', 'in', REPORT_TYPES), ('binding_model_id', '!=', False),
        ], order='id')
        user_groups = self.env.user.all_group_ids
        reports = reports.filtered(lambda report: not report.group_ids or report.group_ids & user_groups)
        # the reports of the app of the model first ("Quotation / Order" of Sales, not the "PDF Quote" an
        # add-on prints)
        module = self.env[record._name]._original_module
        xmlids = reports.get_external_id()
        return reports.sorted(lambda report: (xmlids.get(report.id, '').split('.')[0] != module, report.id))

    @api.model
    def _choose_record_report(self, reports, rest, record):
        """ The report the text names, else the default one. """
        text = rest
        for mention in self._get_mentions():
            text = re.sub(re.escape('@' + mention['name']), ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text.replace(record.display_name, ' ')).strip().lower()
        if text and len(reports) > 1:
            def score(report):
                name = report.name.lower()
                return 1.0 if text in name or name in text else difflib.SequenceMatcher(None, text, name).ratio()
            best = max(reports, key=score)
            if score(best) >= 0.6:
                return best
        return reports[0]

    @api.model
    def _render_record_report(self, report, record, pdf=True):
        """ The report of a record, printed as the current user: ``(file name, content,
        mimetype)``, a PDF, else the page of the report. """
        record.check_access('read')
        if report not in self._get_record_reports(record):
            raise UserError(self.env._("This report can not be printed for %s.", record.display_name))
        Report = self.env['ir.actions.report']
        name = report.name
        if report.print_report_name:
            try:
                name = safe_eval(report.print_report_name, {'object': record, 'time': time}) or name
            except Exception as error:  # noqa: BLE001 - a file name never fails a report
                _logger.info("AI Chat Pro: no file name for report %s of %s: %s", report.report_name, record, error)
        name = re.sub(r'[\\/:*?"<>|]+', '_', str(name)).strip() or 'report'
        if pdf and report.report_type == 'qweb-pdf':
            content, _type = Report._render_qweb_pdf(report.report_name, [record.id])
            return f"{name}.pdf", content, 'application/pdf'
        content, _type = Report._render_qweb_html(report.report_name, [record.id])
        return f"{name}.html", content, 'text/html'
