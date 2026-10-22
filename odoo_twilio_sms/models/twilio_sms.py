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
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TwilioSms(models.Model):
    """SMS sent to every member of a group, now or on a scheduled date"""
    _name = 'twilio.sms'
    _description = 'Twilio SMS'

    name = fields.Char(help='Name of the SMS', required=True)
    partner_id = fields.Many2one('twilio.sms.group',
                                 string='Receiving Group', required=True,
                                 help='Group that receives the SMS')
    template_body_id = fields.Many2one('twilio.sms.template',
                                       string='SMS Template',
                                       help='Template used to fill in the '
                                            'content')
    content = fields.Text(required=True, compute='_compute_content',
                          store=True, readonly=False, precompute=True,
                          help='Text of the SMS')
    scheduled_date = fields.Date(default=fields.Date.today,
                                 help='Date on which the SMS is sent')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('sent', 'Sent'),
    ], default='draft', help='State of the SMS')
    account_id = fields.Many2one('twilio.account', string='Twilio Account',
                                 required=True,
                                 help='Twilio account used to send the SMS')

    @api.depends('template_body_id')
    def _compute_content(self):
        """Copy the template text, keeping custom text without template"""
        for sms in self:
            sms.content = sms.template_body_id.content or sms.content

    def action_confirm_sms(self):
        """Confirm the SMS and send it if it is scheduled for today"""
        result = True
        for sms in self:
            if not sms.partner_id.contact_ids.filtered('phone'):
                raise UserError(self.env._(
                    "The group %s has no members with a phone number.",
                    sms.partner_id.name))
            sms.state = 'confirm'
            if sms.scheduled_date == fields.Date.today():
                result = self.send_sms(sms)
        return result

    def send_sms_on_time(self):
        """Send the confirmed SMS scheduled for today"""
        for sms in self.env['twilio.sms'].search([
                ('state', '=', 'confirm'),
                ('scheduled_date', '=', fields.Date.today())]):
            self.send_sms(sms)

    @api.model
    def send_sms(self, sms):
        """Send the SMS to every group member and report the failures"""
        client = sms.account_id._get_client()
        sent, failed = 0, []
        for partner in sms.partner_id.contact_ids:
            if not partner.phone:
                failed.append(partner.name)
                continue
            try:
                client.messages.create(body=sms.content,
                                       from_=sms.account_id.from_number,
                                       to=partner.phone)
                sent += 1
            except Exception as error:
                _logger.warning("Twilio SMS to %s failed: %s",
                                partner.phone, error)
                failed.append(partner.name)
        # Once anyone received it, the SMS is not sent again
        if sent:
            sms.state = 'sent'
        if not failed:
            message = self.env._("Message sent successfully.")
            notification_type = 'success'
        elif sent:
            message = self.env._("Message not sent to: %s",
                                 ', '.join(failed))
            notification_type = 'warning'
        else:
            message = self.env._("Message not sent to anyone: %s",
                                 ', '.join(failed))
            notification_type = 'danger'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': notification_type,
                'sticky': bool(failed),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
