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
from odoo import fields, models, _
from odoo.exceptions import UserError


class SendGridSendEmails(models.Model):
    _name = "email.api"
    _description = "Email Reports"

    name = fields.Char(string="Name")
    company_name = fields.Char(string="Company Name")
    recipient_name = fields.Char(string="Recipient Name")
    to_email = fields.Char(string="Recipient Email ID")
    to_email_partner_check = fields.Boolean()
    to_email_partner = fields.Many2one("res.partner",
                                       string="Recipient Emails")
    to_email_lead_check = fields.Boolean()
    to_email_lead = fields.Many2one("crm.lead",
                                    string="Recipient Emails")
    to_email_contact_check = fields.Boolean()
    to_email_contact = fields.Many2one("mailing.contact",
                                       string="Recipient Emails")
    to_email_applicant_check = fields.Boolean()
    to_email_applicant = fields.Many2one("hr.applicant",
                                         string="Recipient Emails")
    from_email = fields.Char(string="Sender Email")
    temp_type = fields.Many2one('sendgrid.email.template',
                                string="Email Template")
    send_date = fields.Datetime(string="Send Date", readonly=True,
                                default=fields.Datetime.now)
    error_msg = fields.Text(string="Error Content", readonly=True)
    error_check = fields.Boolean()
    state = fields.Selection([('send', "Send"), ('error', "Error")],
                             readonly=True, string="State", default='send')
    bounce_msg = fields.Text(string="Bounce Message")
    email_finder = fields.Integer(string="Email finder")

    def bounce_check(self):
        """function is used for Checking Email Bounce Status."""
        send_grid_api = self.env['ir.config_parameter'].sudo().get_param(
            'sendgrid_email.send_grid_api_value')
        params = {'email': self.to_email}
        headers = {
            'authorization': "Bearer " + send_grid_api,
            'Content-Type': 'application/json'
        }
        url = "https://api.sendgrid.com/v3/suppression/bounces"
        response = requests.get(url, headers=headers, params=params)
        # Check the response status code
        if response.status_code == 200:
            # Parse the JSON response
            bounce_details = response.json()
            # Check if there are any bounce records for the email
            if 'result' in bounce_details and len(bounce_details['result']) > 0:
                for bounce_record in bounce_details['result']:
                    self.bounce_msg = (f"- Reason: {bounce_record['reason']}",
                                       f"  Status: {bounce_record['status']}")
            else:
                self.bounce_msg = f"No bounce records found for {self.to_email}"
        else:
            self.bounce_msg = f"Error retrieving bounce details: {response.status_code} - {response.text}"

    def send_error_mails(self):
        """function is used for Resending Error State mails."""
        for line in self:
            if line.state == 'error':
                if not line.temp_type:
                    raise UserError(_("It Needs A Template ID"))
                if not line.from_email:
                    raise UserError(_("It Needs A Sender Email!!"))
                else:
                    from_email = line.from_email
                api_key = self.env['ir.config_parameter'].sudo().get_param('sendgrid_email.send_grid_api_value')
                if not api_key and api_key == "":
                    raise UserError(_("Your Company Needs an API Key"))
                if line.to_email and line.recipient_name:
                    payload = json.dumps({
                        "personalizations": [
                            {"to": [{"email": line.to_email}],
                             "subject": line.temp_type.ver_subject}
                        ],
                        "from": {"email": from_email},
                        "content": [
                            {"type": "text/html",
                             "value": line.temp_type.temp_cont}
                        ]
                    })
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    url = "https://api.sendgrid.com/v3/mail/send"
                    response = requests.request("POST", url,
                                                headers=headers,
                                                data=payload)
                    if response.status_code in [200, 201, 202]:
                        line.state = 'send'
                        line.error_check = False
                        line.error_msg = False




