# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#    For full details, see https://www.odoo.com/documentation/20.0/legal/licenses/licenses.html
#
#############################################################################
from odoo import fields, models
from odoo.fields import Command


class SendMailReport(models.TransientModel):
    """Transient model for sending account reports by email."""
    _name = 'send.mail.report'
    _description = "Send Mail Report Wizard"

    partner_id = fields.Many2one('res.partner', string='Recipient',
                                 required=True, help="Select a recipient")
    subject = fields.Char(required=True, help="Subject of the email")
    email_body = fields.Html(string="Content", required=True,
                             help="Body of the email")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments', readonly=True,
        help="Report attachments")
    report = fields.Integer(help="Report ID")

    def action_send_report_mail(self):
        """Send the account PDF report to the recipient's email."""
        self.ensure_one()
        mail_template = self.env.ref(
            'account_report_send_by_mail.email_template_account_report')
        email_values = {
            'email_from': self.env.user.email,
            'email_to': False,
            'recipient_ids': [Command.set(self.partner_id.ids)],
            'subject': self.subject,
            'attachment_ids': [Command.link(att.id) for att in self.attachment_ids],
        }
        mail_template.send_mail(self.id, email_values=email_values,
                                force_send=True)
        return {'type': 'ir.actions.act_window_close'}

    def send_current_report(self):
        """Generate the current accounting PDF report."""
        return self.main_function(False)

    def send_unfolded_report(self):
        """Generate the unfolded accounting PDF report."""
        return self.main_function(True)

    def main_function(self, report_value):
        """Generate and attach the PDF report based on current or unfolded view."""
        report_id = self.env.context.get('report') or self.report
        if not report_id:
            return None
        report = self.env['account.report'].browse(int(report_id))
        if not report.exists():
            return None

        unfolded = self.env.context.get('unfolded_lines')
        report_options = self.env.context.get('report_options') or {}

        previous_options = dict(report_options)
        previous_options['selected_section_id'] = report.id

        if report_value:
            previous_options['unfold_all'] = True
        elif unfolded is not None:
            previous_options['unfolded_lines'] = unfolded

        custom_report_options = report.get_options(previous_options=previous_options)
        custom_report_options['report_id'] = report.id

        try:
            generated_file_data = report.dispatch_report_action(
                custom_report_options, 'export_to_pdf'
            )
        except Exception:
            generated_file_data = report.export_to_pdf(custom_report_options)

        file_content = generated_file_data.get('file_content')
        file_name = generated_file_data.get('file_name') or f"{report.name}.pdf"
        if not file_name.endswith('.pdf'):
            file_name = f"{file_name}.pdf"

        attachment = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'raw': file_content,
            'mimetype': 'application/pdf',
            'res_model': 'account.report',
            'res_id': report.id,
        })
        return attachment.id
