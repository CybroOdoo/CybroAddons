# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from requests.exceptions import RequestException
import werkzeug
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SurveyWhatsapp(models.TransientModel):
    """ Share content to multiple whatsapp number."""
    _name = 'survey.whatsapp'
    _description = "Survey Whatsapp"

    partner_ids = fields.Many2many('res.partner',
                                   string="Recipient",
                                   required=True,
                                   help="Recipients for whatsapp message")
    message = fields.Text(string="Message",
                          default="Dear Participants..We are conducting a "
                                  "survey and your respond would be "
                                  "appreciable.Please answer the following "
                                  "survey",
                          required=True,
                          help="Message body for whatsapp message")
    survey_start_url = fields.Char('Survey URL',
                                   compute='_compute_survey_start_url',
                                   required=True,
                                   help="Url for starting survey")
    answer_dead_line = fields.Date(string="Answer Dead Line",
                                   required=True,
                                   help="Deadline for getting answer")
    survey_id = fields.Many2one('survey.survey',
                                string='Survey',
                                required=True,
                                help="Survey name")

    @api.depends('survey_id')
    def _compute_survey_start_url(self):
        """Automatically fill url of survey"""
        for invite in self:
            invite.survey_start_url = werkzeug.urls.url_join(
                invite.survey_id.get_base_url(),
                invite.survey_id.get_start_url()) if invite.survey_id else False

    def action_send_msg(self):
        """Send content to whatsapp number."""
        if self.partner_ids:
            instant = self.env['configuration.manager'].search([('state', '=', 'verified')], limit=1)
            if not instant:
                raise ValidationError(_("No verified WhatsApp configuration found. Please authenticate first."))
            
            for partner in self.partner_ids:
                if not self.message or not partner.phone:
                    raise ValidationError(_("No Message or not configured phone number for the customer."))
                url = f"https://api.apichat.io/instance{instant.instance}/sendMessage?token={instant.token}"
                sent_message = f"{self.message} {self.survey_start_url} before {str(self.answer_dead_line)}"

                # Clean phone number - keep as string, don't convert to int
                clean_phone = partner.phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').replace('+', '')

                # Ensure phone number has country code
                # If phone doesn't start with country code, try to get it from partner's country
                if len(clean_phone) == 10:  # Likely missing country code
                    if partner.country_id:
                        country_code = partner.country_id.phone_code or ''
                        if country_code:
                            clean_phone = f"{country_code}{clean_phone}"

                # WhatsApp API might expect chatId format: phone@c.us
                chat_id = f"{clean_phone}@c.us"

                # Try different payload formats
                data = {
                    "chatId": chat_id,
                    "body": sent_message
                }
                try:
                    response = requests.post(url, json=data, timeout=30)
                    response.raise_for_status()

                    # Create message record on success
                    self.env['whatsapp.message'].create({
                        'status': 'sent',
                        'from_user': self.env.user.id,
                        'to_user': partner.phone,
                        'body': sent_message
                    })
                except RequestException as e:
                    raise ValidationError(_(f"Failed to send WhatsApp message to {partner.name}: {str(e)}\nPhone: {clean_phone}\nChatId: {chat_id}\nPlease check the phone number format and API credentials."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('WhatsApp messages sent successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }
