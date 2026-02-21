# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models
from odoo.exceptions import ValidationError


class VapiInboundCall(models.Model):
    """This model is used to register and manage phone numbers that are
     connected to virtual AI assistants via the Vapi.ai platform,
     supporting both single and multi-language flows."""
    _name = "vapi.inbound.call"
    _inherit = "mail.thread"
    _description = "Vapi Inbound Call"
    _rec_name = "phone_number"

    assistant_name_id = fields.Many2one('ora.ai',
                                        string="Assistant",
                                        help="The AI Assistant to associate"
                                             "with this phone number.")
    id_assistant = fields.Char(string="Assistant ID",
                               related="assistant_name_id.id_assistant",
                               help="The unique identifier of the assistant.")
    phone_number = fields.Char(string="Phone Number", required=True,
                               help="The Twilio phone number to register"
                                    "on Vapi.ai.")
    twilio_sid = fields.Char(string="Twilio Account SID", required=True,
                             help="The Twilio Account SID required for"
                                  "authentication.")
    twilio_auth_token = fields.Char(string="Twilio Auth Token", required=True,
                                    help="The Twilio authentication token.")
    id_phone_number = fields.Char(string="Phone numberID",
                                  help="The internal ID of the phone number"
                                       "returned by Vapi.ai.")
    squad_id = fields.Many2one('vapi.squad', string="Squad Id",
                               help="If using multi-language, select the squad"
                                    "to assign the number to.")
    is_lang_switch = fields.Boolean(string="Multi-Language",
                                    help="Enable this if the number should "
                                         "use a squad (multi-language) instead"
                                         " of a single assistant.")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             'State', readonly=True, default='draft',
                             help="The current state of the phone number "
                                  "registration.")

    def action_set_number(self):
        """Registers the provided Twilio phone number with the VAPI AI
         platform."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        if not bearer:
            raise ValidationError(
                "Please add the Vapi credentials in the Settings.")
        url = "https://api.vapi.ai/phone-number"
        payload = {
            "provider": "twilio",
            "number": self.phone_number,
            "twilioAccountSid": self.twilio_sid,
            "twilioAuthToken": self.twilio_auth_token,
            "serverUrl": f"{base_url}/vapi_voice_assistant/status",
            "name": "odoo"
        }
        if self.is_lang_switch:
            payload["squadId"] = self.squad_id.id_squad
        else:
            payload["assistantId"] = self.id_assistant
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload,
                                    headers=headers)
        json_response = response.json()
        if json_response.get('statusCode') == 400:
            raise ValidationError(json_response.get('message'))
        self.write({
            'state': 'done',
            'id_phone_number': json_response.get('id')
        })

    def write(self, vals):
        """ Overrides the write method to automatically update the
        phone number configuration on Vapi.ai when key fields are modified."""
        res = super().write(vals)
        if self.id_phone_number:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            bearer = self.env['ir.config_parameter'].sudo().get_param(
                'ora_ai_base.vapi_private_api_key')
            url = f"https://api.vapi.ai/phone-number/{self.id_phone_number}"
            payload = {
                "serverUrl": f"{base_url}/vapi_voice_assistant/status"}
            if self.is_lang_switch:
                payload["squadId"] = self.squad_id.id_squad
            else:
                payload["assistantId"] = self.id_assistant
            headers = {"Authorization": "Bearer" + bearer + "",
                       "Content-Type": "application/json"}
            requests.request("PATCH", url, json=payload,
                             headers=headers)
        return res

    def unlink(self):
        """Deletes the registered phone number from Vapi.ai before
        removing the record locally."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_voice_assistant_base.vapi_private_api_key')
        for rec in self:
            url = f"https://api.vapi.ai/phone-number/{rec.id_phone_number}"
            headers = {
                "Authorization": f"Bearer {bearer}"}
            requests.request("DELETE", url, headers=headers)
        return super().unlink()
