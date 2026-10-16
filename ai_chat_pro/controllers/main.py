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

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

PRINT_SCRIPT = b'<script>window.addEventListener("load", () => setTimeout(() => window.print(), 300));</script>'


class AiChatProController(http.Controller):

    @http.route('/ai_chat_pro/export/xlsx', type='http', auth='user', methods=['POST'])
    def export_xlsx(self, message_id, **kwargs):
        """ Download the table of an answer as an Excel file. Access is checked on the
        message, as the current user. """
        message = request.env['ai.chat.message'].browse(int(message_id)).exists()
        if not message:
            raise request.not_found()
        file_name, content = message._export_xlsx()
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(file_name)),
        ])

    @http.route('/ai_chat_pro/report/pdf', type='http', auth='user', methods=['POST'])
    def report_pdf(self, message_id, chart=None, **kwargs):
        """ Download an answer as a PDF report, printed by the report engine of Odoo, with
        the chart the web client drew. Access is checked on the message, as the current
        user. """
        message = request.env['ai.chat.message'].browse(int(message_id)).exists()
        if not message:
            raise request.not_found()
        file_name, content = message._render_pdf_report(chart=chart or None)
        return request.make_response(content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(file_name)),
        ])

    @http.route('/ai_chat_pro/report/html', type='http', auth='user', methods=['POST'])
    def report_html(self, message_id, chart=None, **kwargs):
        """ Open the report of an answer as a page, to print it from the browser when the
        server has no PDF engine. Access is checked on the message, as the current user. """
        message = request.env['ai.chat.message'].browse(int(message_id)).exists()
        if not message:
            raise request.not_found()
        html = message._render_html_report(chart=chart or None)
        # the print dialog opens once the page is drawn: "Save as PDF" makes the file
        html = html.replace(b'</body>', PRINT_SCRIPT + b'</body>', 1)
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route('/ai_chat_pro/record_report/<int:report_id>/<string:model>/<int:res_id>', type='http', auth='user',
                methods=['GET'])
    def record_report(self, report_id, model, res_id, **kwargs):
        """ Print a report of a record, as its Print menu does: a PDF when the server
        prints them, else the page of the report with the print window of the browser
        ("Save as PDF"). Access is checked on the record, as the current user. """
        if model not in request.env:
            raise request.not_found()
        record = request.env[model].browse(res_id).exists()
        report = request.env['ir.actions.report'].sudo().browse(report_id).exists()
        if not record or not report:
            raise request.not_found()
        pdf = request.env['ai.chat.message']._has_pdf_engine()
        file_name, content, mimetype = request.env['ai.chat.assistant']._render_record_report(report, record, pdf=pdf)
        if mimetype == 'application/pdf':
            return request.make_response(content, headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(content)),
                ('Content-Disposition', content_disposition(file_name, disposition_type='inline')),
            ])
        content = content if isinstance(content, bytes) else content.encode()
        content = content.replace(b'</body>', PRINT_SCRIPT + b'</body>', 1)
        return request.make_response(content, headers=[('Content-Type', 'text/html; charset=utf-8')])
