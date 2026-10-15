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
import binascii
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)

REPORT_REF = 'ai_chat_pro.action_report_ai_answer'
# answers whose data makes a report: tables and key figures
REPORT_RESULT_TYPES = ('table', 'value')
# a table this wide is printed on a landscape page
LANDSCAPE_COLUMNS = 6
# the chart drawn by the web client, sent as a PNG image with the request
MAX_CHART_SIZE = 5 * 1024 * 1024
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
# rows of data given to Odoo's AI service to write the summary of a report
MAX_SUMMARY_ROWS = 30
MAX_INSIGHTS = 4


class AiChatMessage(models.Model):
    _inherit = 'ai.chat.message'

    report_summary = fields.Json(
        help="Executive summary of the PDF report of the answer, written by Odoo's AI service once, then reused.",
    )

    def _can_print_report(self):
        """ Whether an answer makes a PDF report: an answer saved with data, a table of
        records or key figures, not an error nor a record to create. """
        self.ensure_one()
        result = self.result or {}
        return (
            self.role == 'assistant' and not self.is_error and result.get('type') in REPORT_RESULT_TYPES
            # a table without any record makes no report
            and (result['type'] != 'table' or bool(result.get('rows')))
        )

    def _get_report_question(self):
        """ The question the answer replies to. """
        self.ensure_one()
        question = self.env['ai.chat.message'].search([
            ('conversation_id', '=', self.conversation_id.id), ('role', '=', 'user'), ('id', '<', self.id),
        ], order='id desc', limit=1)
        return question.content or ''

    def _get_report_summary(self):
        """ The executive summary of the report: written by Odoo's AI service from the
        data of the answer when the analysis with Odoo AI is enabled, else the text of
        the answer. Written once, then reused. """
        self.ensure_one()
        if self.report_summary:
            return self.report_summary
        summary = {'text': self.content or '', 'insights': []}
        if str2bool(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.use_olg') or 'False', False):
            written = self.env['ai.chat.assistant']._write_report_summary(
                self._get_report_question(), self.result, self.content or '',
            )
            if written:
                summary = written
                # the messages are not written by their users: the summary is kept as the assistant
                self.sudo().report_summary = summary
        return summary

    def _render_pdf_report(self, chart=None):
        """ The answer as a PDF report, printed by the report engine of Odoo, as the
        current user: only the users who can read the answer can print it.

        :param str chart: the chart of the answer drawn by the web client, as a PNG
            image in base64 (``data:image/png;base64,...`` or the base64 alone)
        :return: ``(file name, content)``
        """
        self.ensure_one()
        self.check_access('read')
        if not self._can_print_report():
            raise UserError(self.env._("This answer has no data to make a report of."))
        data = {'chart': self._check_report_chart(chart)} if chart else {}
        columns = (self.result or {}).get('columns') or []
        Report = self.env['ir.actions.report'].with_context(landscape=len(columns) > LANDSCAPE_COLUMNS)
        content, _content_type = Report._render_qweb_pdf(REPORT_REF, self.ids, data=data)
        return f"{self._get_report_file_name()}.pdf", content

    def _render_html_report(self, chart=None):
        """ The answer as the HTML page of its report, to print from the browser when
        the server has no PDF engine. Same report, same access checks as the PDF. """
        self.ensure_one()
        self.check_access('read')
        if not self._can_print_report():
            raise UserError(self.env._("This answer has no data to make a report of."))
        data = {'chart': self._check_report_chart(chart)} if chart else {}
        html, _content_type = self.env['ir.actions.report']._render_qweb_html(REPORT_REF, self.ids, data=data)
        return html

    @api.model
    def _has_pdf_engine(self):
        """ Whether the server has the engine printing PDF reports (wkhtmltopdf):
        without it, reports are printed from the browser. """
        Report = self.env['ir.actions.report']
        return Report.get_wkhtmltopdf_state() in ('ok', 'upgrade')

    def _check_report_chart(self, chart):
        """ The chart sent by the web client, as the data URL of a PNG image: anything
        else is refused, as it is printed in the report. """
        chart = chart.split(',', 1)[1] if chart.startswith('data:') else chart
        try:
            image = base64.b64decode(chart, validate=True)
        except (binascii.Error, ValueError):
            raise UserError(self.env._("The chart of the report could not be read."))
        if len(image) > MAX_CHART_SIZE or not image.startswith(PNG_SIGNATURE):
            raise UserError(self.env._("The chart of the report must be a PNG image."))
        return f"data:image/png;base64,{chart}"

    def _get_report_title(self):
        """ The title of the report: written by Odoo's AI service with its summary, else
        what its data is. The question of the user is never printed. """
        self.ensure_one()
        return self._get_report_summary().get('title') or self._get_report_subtitle() or self.env._("AI Report")

    def _get_report_subtitle(self):
        """ What the data of the report is, as the answer heads it. """
        self.ensure_one()
        result = self.result or {}
        return result.get('heading') or result.get('title') or ''

    def _get_report_file_name(self):
        date = fields.Date.to_string(fields.Date.context_today(self))
        name = re.sub(r'[^\w-]+', '_', self._get_report_title()).strip('_')[:60] or 'report'
        return f"{name}_{date}"


class AiChatAssistant(models.AbstractModel):
    _inherit = 'ai.chat.assistant'

    @api.model
    def _write_report_summary(self, question, result, content):
        """ The executive summary of a report, written by Odoo's AI service from the
        data of the answer: a title, a paragraph and a few insights. ``None`` when the
        service does not answer. The question tells what the data is for: it is not
        printed in the report. """
        lines = []
        if result.get('type') == 'table':
            # a count is a number of records (order lines, invoices...), not a quantity
            lines.append(" | ".join(
                f"{column['label']} (number of records)" if column.get('kind') == 'count' else column['label']
                for column in result.get('columns') or []
            ))
            lines += [" | ".join(str(cell)[:60] for cell in row['cells'])
                      for row in (result.get('rows') or [])[:MAX_SUMMARY_ROWS]]
        else:
            lines += [f"{item['label']}: {item['value']}" for item in _get_key_figures(result)]
        prompt = (
            "You write the executive summary of a business report, for managers. Use only the data below, from "
            "the user's Odoo database: no figure that is not in it, no advice that it does not support. Reply in "
            "plain text, in the language of the question. First a line \"Title: \" followed by a short title for "
            "the report, of at most 8 words, in title case, naming what the data shows (not the question as asked). "
            "Then a paragraph of 2 to 4 sentences answering the question, without repeating or quoting it. Then up "
            f"to {MAX_INSIGHTS} key insights, one per line, each starting with \"- \".\n"
            f"Question: {question}\nAnswer: {content}\nData:\n" + "\n".join(lines)
        )
        try:
            text = self._text_chat(prompt)
        except UserError as error:
            _logger.info("AI Chat Pro: no summary for a report: %s", error)
            return None
        title, paragraphs, insights = '', [], []
        for line in (text or '').splitlines():
            line = line.strip().strip('*').strip()
            if match := re.match(r'^title\s*:\s*(.+)$', line, re.IGNORECASE):
                title = match.group(1).strip().strip('"“”*').strip()
            elif re.match(r'^[-*•]\s+', line):
                insights.append(re.sub(r'^[-*•]\s+', '', line))
            elif line and not insights:
                paragraphs.append(line)
        if not paragraphs:
            return None
        return {'title': title[:90], 'text': ' '.join(paragraphs), 'insights': insights[:MAX_INSIGHTS]}


class ReportAiAnswer(models.AbstractModel):
    """ The values of the PDF report of an answer of the assistant. """
    _name = 'report.ai_chat_pro.report_ai_answer'
    _description = "AI Chat Pro Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        messages = self.env['ai.chat.message'].browse(docids)
        messages.check_access('read')
        data = data or {}
        reports = {}
        for message in messages:
            if not message._can_print_report():
                raise UserError(self.env._("This answer has no data to make a report of."))
            result = message.result
            reports[message.id] = {
                # the question of the user is not printed: the report is titled after its data
                'summary': message._get_report_summary(),
                'title': message._get_report_title(),
                'subtitle': message._get_report_subtitle(),
                'figures': _get_key_figures(result) if result.get('type') == 'value' else [],
                'columns': result.get('columns') or [],
                'rows': result.get('rows') or [],
                'total': result.get('total') or len(result.get('rows') or []),
                'tags': result.get('tags') or [],
                'chart': data.get('chart'),
                'author': message.user_id.name or self.env.user.name,
                'date': message.create_date,
            }
        return {
            'doc_ids': docids,
            'doc_model': 'ai.chat.message',
            'docs': messages,
            'reports': reports,
            'printed_by': self.env.user.name,
        }


def _get_key_figures(result):
    """ The figures of a key-figure answer: a count, or the aggregates of the records. """
    if result.get('rows') and result.get('columns'):
        return [
            {'label': column['label'], 'value': result['rows'][0]['cells'][index]}
            for index, column in enumerate(result['columns'])
        ]
    return [{'label': result.get('label') or '', 'value': result.get('value')}]

