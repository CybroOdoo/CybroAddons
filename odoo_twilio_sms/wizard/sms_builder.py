# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from twilio.base.exceptions import TwilioException


class SmsBuilder(models.TransientModel):
    """Wizard to send one SMS to a contact"""
    _name = 'sms.builder'
    _description = 'SMS Builder'

    partner_id = fields.Many2one('res.partner', string='Recipient',
                                 help='Contact who receives the SMS')
    receiving_number = fields.Char(required=True,
                                   compute='_compute_receiving_number',
                                   store=True, readonly=False,
                                   precompute=True,
                                   help='Phone number the SMS is sent to')
    template_id = fields.Many2one('twilio.sms.template',
                                  string='Select Template',
                                  help='Template used to fill in the '
                                       'message')
    text_message = fields.Text(string='Message', required=True,
                               compute='_compute_text_message',
                               store=True, readonly=False,
                               precompute=True,
                               help='Text of the SMS')
    account_id = fields.Many2one('twilio.account', string='Twilio Account',
                                 required=True,
                                 help='Twilio account used to send the SMS')

    @api.depends('partner_id')
    def _compute_receiving_number(self):
        """Suggest the recipient's phone without changing the contact"""
        for wizard in self:
            wizard.receiving_number = (wizard.partner_id.phone
                                       or wizard.receiving_number)

    @api.depends('template_id')
    def _compute_text_message(self):
        """Copy the template text, keeping custom text without template"""
        for wizard in self:
            wizard.text_message = (wizard.template_id.content
                                   or wizard.text_message)

    def action_confirm_sms(self):
        """Send the SMS through the Twilio account"""
        self.ensure_one()
        try:
            message = self.account_id._get_client().messages.create(
                body=self.text_message,
                from_=self.account_id.from_number,
                to=self.receiving_number)
            sent = bool(message.sid)
        except TwilioException:
            sent = False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': (self.env._("Message sent.") if sent
                            else self.env._("Message not sent.")),
                'type': 'success' if sent else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
