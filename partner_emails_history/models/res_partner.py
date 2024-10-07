# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """This is used to add the email history functionality"""
    _inherit = 'res.partner'

    is_show_sms = fields.Boolean(string="Show sms history",
                                 help="Visibility of sms history",
                                 config_parameter='partner_emails_history'
                                                  '.default_is_sms_history')
    is_show_emails = fields.Boolean(string="Show email history",
                                    help="Visibility of email history",
                                    config_parameter='partner_emails_history'
                                                     '.default_is_email_history')
    sms_count = fields.Integer(string="Sms Count",
                               help="Count of total sms of the customer",
                               compute="_compute_sms")
    received_email_count = fields.Integer(string="Received Email Count",
                                          help="Count of total received "
                                               "emails for the customer",
                                          compute="_compute_email")
    send_email_count = fields.Integer(string="Send EmailCount",
                                      help="Count of emails send by the "
                                           "customer",
                                      compute="_compute_email")

    def _compute_email(self):
        """This is used to compute the count of emails"""
        for rec in self:
            message_from = rec.env['mail.message'].search(
                [('email_from', 'ilike', self.email)])
            rec.send_email_count = len(message_from)

            message_to = rec.env['mail.message'].search(
                [('partner_ids', 'in', self.id)])
            rec.received_email_count = len(message_to)

    def _compute_sms(self):
        """This is used to compute the count of sms"""
        for rec in self:
            count = rec.env['sms.sms'].search([('partner_id', '=', rec.id)])
            rec.sms_count = len(count)

    def action_view_partner_sms(self):
        """This is used to visible the sms of the partner"""
        self.ensure_one()
        action = self.env.ref('sms.sms_sms_action').read()[0]
        action['domain'] = [
            ('partner_id', '=', self.id)]
        return action

    def sent_email_history(self):
        """This is used to visible the send emails of the partner"""
        action = self.env.ref('mail.action_view_mail_message')
        result = action.read()[0]
        result['domain'] = [('email_from', 'ilike', self.email)]
        return result

    def received_email_history(self):
        """This is used to visible the received emails of the partner"""
        action = self.env.ref('mail.action_view_mail_message')
        result = action.read()[0]
        result['domain'] = [('partner_ids', 'in', self.id)]
        return result
