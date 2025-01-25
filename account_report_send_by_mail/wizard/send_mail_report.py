# -*- coding: utf-8 -*-
################################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
import base64
import markupsafe
from odoo import fields, models


class SendMailReport(models.TransientModel):
    """Created a new transient model for send mail"""
    _name = 'send.mail.report'
    _description = "Display send mail wizard details"

    partner_id = fields.Many2one('res.partner', string='Recipient',
                                 required=True, help="Select one recipient")
    subject = fields.Char(string='Subject', required=True,
                          help="Subject of the email")
    email_body = fields.Html(required=True, String="Content",
                             help="Body of the email")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments', readonly=True,
        help="Report attachment ")
    report = fields.Integer(string="Report", help="report id")

    def send_current_report(self):
        """Create current accounting PDF report"""
        report_value = False
        return self.main_function(report_value)

    def send_unfolded_report(self):
        """Create unfolded PDF report"""
        report_value = True
        return self.main_function(report_value)

    def main_function(self, report_value):
        """Report action of current report and unfolded report
         pdf is generated"""
        report_id = self.env.context.get('report')
        unfolded = self.env.context.get('unfolded_lines')
        custom_context = {
            'mode': 'print',
            'base_url': self.env['ir.config_parameter'].sudo().get_param(
                'report.url') or
                        self.env['ir.config_parameter'].sudo().get_param(
                            'web.base.url'),
            'company': self.env.company,
        }
        if self.report:
            custom_reports_to_print = self.env['account.report'].browse(
                self.report)
        else:
            custom_reports_to_print = self.env['account.report'].browse(
                report_id)
            self.report = report_id
        custom_bodies = []
        max_custom_col_number = 0
        for custom_report in custom_reports_to_print:
            if not report_value:
                custom_report_options = custom_report.get_options(
                    previous_options={'selected_section_id': custom_report.id,
                                      'unfolded_lines': unfolded}
                )
            else:
                custom_report_options = custom_report.get_options(
                    previous_options={'selected_section_id': custom_report.id,
                                      'unfold_all': True}
                )
            max_custom_col_number = max(max_custom_col_number,
                                        len(custom_report_options[
                                                'columns']) * len(
                                            custom_report_options[
                                                'column_groups']))
            custom_bodies.append(custom_report._get_pdf_export_html(
                custom_report_options,
                custom_report._filter_out_folded_children(
                    custom_report._get_lines(custom_report_options)),
                additional_context={'base_url': self.env[
                                                    'ir.config_parameter'].sudo().get_param(
                    'report.url') or self.env[
                                                    'ir.config_parameter'].sudo().get_param(
                    'web.base.url')}
            ))
        custom_footer_data = self.env['ir.actions.report']._render_template(
            "account_reports.internal_layout", values=custom_context)
        footer_decode = custom_footer_data.decode()
        custom_footer = self.env['ir.actions.report']._render_template(
            "web.minimal_layout", values=dict(custom_context, subst=True,
                                              body=markupsafe.Markup(
                                                  footer_decode)))
        custom_file_content = self.env['ir.actions.report']._run_wkhtmltopdf(
            custom_bodies,
            footer=custom_footer.decode(),
            landscape=max_custom_col_number > 5,
            specific_paperformat_args={
                'data-report-margin-top': 10,
                'data-report-header-spacing': 10,
                'data-report-margin-bottom': 15,
            }
        )
        if report_id:
            report_name = self.env['account.report'].browse(report_id).name
            attachment_values = {'name': f"""{report_name}.pdf""",
                                 'type': 'binary',
                                 'datas': base64.b64encode(custom_file_content),
                                 'mimetype': 'application/pdf',
                                 'res_model': 'account.report',
                                 'res_id': report_id}
            attachment = self.env['ir.attachment'].sudo().create(
                attachment_values)
            return attachment.id

    def action_send_report_mail(self):
        """Action for send account PDF report to recipient mail"""
        mail_template = (self.env.ref(
            'account_report_send_by_mail.email_template_account_report'))
        email_values = {'email_from': self.env.user.email,
                        'email_to': self.partner_id.email,
                        'subject': self.subject,
                        'attachment_ids': [(4, self.attachment_ids.id)],
                        }
        mail_template.send_mail(self.id, email_values=email_values,
                                force_send=True)
        mail_template.attachment_ids = [(5, 0, 0)]
