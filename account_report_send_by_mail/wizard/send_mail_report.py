# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
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
