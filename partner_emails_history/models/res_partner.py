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

CONFIG_PREFIX = 'partner_emails_history.'


class ResPartner(models.Model):
    """This is used to add the email history functionality"""
    _inherit = 'res.partner'

    is_show_sms = fields.Boolean(string="Show SMS History",
                                 help="Visibility of SMS history",
                                 compute="_compute_show_history")
    is_show_emails = fields.Boolean(string="Show Email History",
                                    help="Visibility of email history",
                                    compute="_compute_show_history")
    sms_count = fields.Integer(string="SMS Count",
                               help="Count of total SMS of the customer",
                               compute="_compute_sms")
    received_email_count = fields.Integer(string="Received Email Count",
                                          help="Count of total received "
                                               "emails for the customer",
                                          compute="_compute_email")
    send_email_count = fields.Integer(string="Sent Email Count",
                                      help="Count of emails sent by the "
                                           "customer",
                                      compute="_compute_email")

    @api.model
    def _get_history_flag(self, key):
        """Return the boolean value of a history setting."""
        value = self.env['ir.config_parameter'].sudo().get_str(
            CONFIG_PREFIX + key)
        return bool(value) and value != 'False'

    def _compute_show_history(self):
        """Compute the visibility of the history buttons from the settings.
        The master toggle must be enabled for any button to be shown."""
        show_history = self._get_history_flag('default_is_history')
        show_sms = show_history and self._get_history_flag(
            'default_is_sms_history')
        show_emails = show_history and self._get_history_flag(
            'default_is_email_history')
        for rec in self:
            rec.is_show_sms = show_sms
            rec.is_show_emails = show_emails

    def _get_sent_email_domain(self):
        """Domain of the messages sent by the partner."""
        self.ensure_one()
        domain = [('author_id', '=', self.id)]
        if self.email:
            domain = ['|', ('email_from', 'ilike', self.email)] + domain
        return domain

    def _get_received_email_domain(self):
        """Domain of the messages received by the partner."""
        self.ensure_one()
        return [('partner_ids', 'in', [self.id])]

    def _compute_email(self):
        """This is used to compute the count of emails"""
        message = self.env['mail.message'].sudo()
        for rec in self:
            if not rec.id:
                rec.send_email_count = 0
                rec.received_email_count = 0
                continue
            rec.send_email_count = message.search_count(
                rec._get_sent_email_domain())
            rec.received_email_count = message.search_count(
                rec._get_received_email_domain())

    def _compute_sms(self):
        """This is used to compute the count of sms"""
        sms = self.env['sms.sms'].sudo()
        for rec in self:
            rec.sms_count = sms.search_count(
                [('partner_id', '=', rec.id)]) if rec.id else 0

    def action_view_partner_sms(self):
        """This is used to visible the sms of the partner"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sms.sms_sms_action')
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    def sent_email_history(self):
        """This is used to visible the sent emails of the partner"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'mail.action_view_mail_message')
        action['domain'] = self._get_sent_email_domain()
        return action

    def received_email_history(self):
        """This is used to visible the received emails of the partner"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'mail.action_view_mail_message')
        action['domain'] = self._get_received_email_domain()
        return action
