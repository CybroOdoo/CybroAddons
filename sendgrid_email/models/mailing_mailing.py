# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Noushid Khan.P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
import json
import requests
from odoo import models, fields, api


class SendGridEmail(models.Model):
    _inherit = 'mailing.mailing'

    email_temp = fields.Many2one("sendgrid.email.template",
                                 string="Email Template")
    sender_id = fields.Many2one('mailing.contact', string="Sender")
    to_email_partner_check = fields.Boolean()
    to_email_partner_ids = fields.Many2many("res.partner",
                                            string="Recipient Emails")
    to_email_lead_check = fields.Boolean()
    to_email_lead = fields.Many2many("crm.lead",
                                     string="Recipient Emails")
    to_email_contact_check = fields.Boolean()
    to_email_contact = fields.Many2many("mailing.contact",
                                        string="Recipient Emails")
    to_email_applicant_check = fields.Boolean()
    to_email_applicant = fields.Many2many("hr.applicant",
                                          string="Recipient Emails")
    email_finder = fields.Integer(string="Email finder")
    sent_count = fields.Integer(string="Send Count")
    temp_check = fields.Boolean()

    def action_send_grid(self):
        """Function for sending emails using the SendGrid API and
        logging the results."""
        api_key = self.env["ir.config_parameter"].sudo().get_param(
            "sendgrid_email.send_grid_api_value")
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        # Helper function to send an individual email
        def send_individual_email(recipient_email):
            if not recipient_email:
                return None
            payload = json.dumps({
                "personalizations": [
                    {"to": [{"email": recipient_email}],
                     "subject": self.subject}
                ],
                "from": {"email": self.sender_id.email},
                "content": [{"type": "text/html", "value": self.body_arch}]
            })
            try:
                response = requests.post(url, headers=headers, data=payload)
                return response
            except Exception as e:
                return None

        # Helper function to handle email responses and log the result
        def log_email_result(recipient, email_field, type_check_field, model_name):
            common_data = {
                'name': self.subject,
                'to_email_partner': recipient.id,
                'to_email': recipient[email_field],
                'recipient_name': recipient.name,
                'company_name': getattr(recipient, 'company_name',
                                        "") or getattr(recipient.company_id,
                                                       'name', ""),
                'from_email': self.sender_id.email,
                'temp_type': self.email_temp.id,
                'email_finder': self.id,
                type_check_field: True
            }
            response = send_individual_email(recipient[email_field])
            if response.status_code in [200, 201, 202]:
                common_data.update({'state': 'send'})
                self.env["email.api"].create(common_data)
            else:
                error_data = response.json().get('errors', [{}])
                error_msg = error_data[0].get('message',
                                              'Unknown error') if error_data else 'Unknown error'
                common_data.update({'state': 'error', 'error_msg': error_msg,
                                    'error_check': True})
                self.env["email.api"].create(common_data)
        # Email recipient mappings
        recipient_mappings = [
            (self.to_email_partner_ids, 'email', 'to_email_partner_check','res.partner'),
            (self.to_email_lead, 'email_from', 'to_email_lead_check', 'crm.lead'),
            (self.to_email_contact, 'email', 'to_email_contact_check', 'mailing.contact'),
            (self.to_email_applicant, 'email_from', 'to_email_applicant_check', 'hr.applicant'),
        ]
        # Process each recipient type
        for recipients, email_field, type_check_field, model_name in recipient_mappings:
            if recipients:
                for recipient in recipients:
                    log_email_result(recipient, email_field, type_check_field, model_name)

    @api.onchange('email_temp', 'mailing_model_id', 'contact_list_ids')
    def temp_details(self):
        """function used for filling subject and recipients emails
        based on template and recipient emails"""
        if self.email_temp:
            self.temp_check = True
            self.body_arch = self.email_temp.temp_cont
            self.body_html = self.email_temp.temp_cont
            self.subject = self.email_temp.ver_subject
        else:
            self.temp_check = False
        if self.mailing_model_real == "sale.order" or self.mailing_model_real == "event.registration" or self.mailing_model_real == "event.track":
            self.to_email_contact = False
            self.to_email_lead = False
            self.to_email_applicant = False
            self.mailing_domain = "[]"
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_partner_ids = email_ids.partner_id
        elif self.mailing_model_real == "crm.lead":
            self.to_email_contact = False
            self.to_email_partner_ids = False
            self.to_email_applicant = False
            self.mailing_domain = "[]"
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_lead = email_ids
        elif self.mailing_model_real == "mailing.contact":
            self.to_email_partner_ids = False
            self.to_email_lead = False
            self.to_email_applicant = False
            self.mailing_domain = "[]"
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_contact = email_ids
            if self.contact_list_ids:
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data),
                     ('list_ids', '=', self.contact_list_ids.ids)])
                self.to_email_contact = email_ids
        elif self.mailing_model_real == "hr.applicant":
            self.to_email_contact = False
            self.to_email_lead = False
            self.to_email_partner_ids = False
            self.mailing_domain = "[]"
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_applicant = email_ids
        else:
            self.to_email_contact = False
            self.to_email_lead = False
            self.to_email_applicant = False
            self.mailing_domain = "[]"
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_partner_ids = email_ids

    @api.onchange('mailing_domain')
    def get_mails_recipients(self):
        """function used for filtering based on domain filter"""
        if self.mailing_model_real == "sale.order" or self.mailing_model_real == "event.registration" or self.mailing_model_real == "event.track":
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_partner_ids = email_ids.partner_id
        elif self.mailing_model_real == "crm.lead":
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_lead = email_ids
        elif self.mailing_model_real == "mailing.contact":
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_contact = email_ids
        elif self.mailing_model_real == "hr.applicant":
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_applicant = email_ids
        else:
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                email_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
                if email_ids:
                    self.to_email_partner_ids = email_ids

    @api.onchange('to_email_partner_ids', 'to_email_lead',
                  'to_email_contact', 'to_email_applicant')
    def show_hide_fields(self):
        """function is used for Enabling Needed recipient mail
        fields by changing check box values."""
        if self.to_email_partner_ids:
            self.to_email_partner_check = True
        else:
            self.to_email_partner_check = False
        if self.to_email_lead:
            self.to_email_lead_check = True
        else:
            self.to_email_lead_check = False
        if self.to_email_contact:
            self.to_email_contact_check = True
        else:
            self.to_email_contact_check = False
        if self.to_email_applicant:
            self.to_email_applicant_check = True
        else:
            self.to_email_applicant_check = False

    def _action_view_documents_filtered(self, view_filter):
        """function is used for returning send view in needed recipient tree view"""
        if view_filter == 'sent':
            res_ids = []
            for mass_mailing in self:
                mai_data = mass_mailing.sudo()._get_recipients()
                res_ids = self.env[self.mailing_model_real].search(
                    [('id', '=', mai_data)])
            model_name = self.env['ir.model']._get(
                self.mailing_model_real).display_name
            return {
                'name': model_name,
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'res_model': self.mailing_model_real,
                'domain': [('id', 'in', res_ids.ids)],
                'context': dict(self._context, create=False)
            }
        else:
            return super(SendGridEmail, self)._action_view_documents_filtered(
                view_filter)
