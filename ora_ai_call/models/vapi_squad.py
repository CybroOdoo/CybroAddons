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
import logging
import requests
from odoo import fields, models

_logger = logging.getLogger(__name__)


class VapiSquad(models.Model):
    """A Vapi Squad is a logical grouping of assistant members that can be
     managed and synchronized with the external Vapi.ai API."""
    _name = "vapi.squad"
    _description = "Vapi Squad"
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']


    name = fields.Char(string="Name", required=True,
                       help="The name of the squads.")
    assistant_id = fields.Many2one('ora.ai',
                                   string='First Assistant',
                                   help="Name of the first assistant of the"
                                        " squad.")
    assistant_ids = fields.One2many('squad.members.line',
                                    'squad_id',
                                    string='Members',
                                    help="All assistant  members in the"
                                         " squads.")
    date = fields.Date(string="Date", readonly=True,
                       help="The date on which the squad was created.")
    id_squad = fields.Char(string="Squad ID", readonly=True, tracking=True,
                           help="The unique identifier of the squad as "
                                "returned by the external Vapi API")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             'State', readonly=True, default="draft",
                             copy=False, tracking=True,
                             help="State of the squad.")

    def action_create_squad(self):
        """Creates a new squad on the external Vapi.ai platform and updates
        the current record with the result."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        url = "https://api.vapi.ai/squad"
        members = self.assistant_ids
        assistant_id_list = self.assistant_ids.mapped('assistant_id').mapped(
            'id_assistant')
        payload = {
            "name": self.name,
            "members": [{
                "assistantId": self.assistant_id.id_assistant,
                "assistantDestinations": [
                    {
                        "type": "assistant",
                        "transferMode": rec.transfer_modes,
                        "assistantName": rec.assistant_id.name,
                        "description": rec.description,
                        "message": rec.message,
                    } for rec in members
                ],
            }]
        }
        for assistant_id in assistant_id_list:
            payload["members"].append({"assistantId": assistant_id})
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload,
                                    headers=headers)
        json_response = response.json()
        self.write({'date': json_response.get('createdAt'),
                    'state': 'done',
                    'id_squad': json_response.get('id')
                    })

    def unlink(self):
        """Overrides the unlink method to also delete the squad from
         the external Vapi API."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        for rec in self:
            url = f"https://api.vapi.ai/squad/{rec.id_squad}"
            headers = {"Authorization": f"Bearer {bearer}"}
            response = requests.request("DELETE", url, headers=headers)
            if response.status_code != 200:
                _logger.warning(
                    f"Failed to delete squad {rec.id_squad}: {response.text}")
        return super().unlink()

    def write(self, vals):
        """Overrides the default `write` method to update the corresponding
         squad on the external Vapi API whenever relevant fields are
         modified."""
        res = super().write(vals)
        if self.id_squad:
            bearer = self.env['ir.config_parameter'].sudo().get_param(
                'ora_ai_base.vapi_private_api_key')
            url = f"https://api.vapi.ai/squad/{self.id_squad}"
            assistant_id_list = self.assistant_ids.mapped(
                'assistant_id').mapped('id_assistant')
            payload = {
                "name": self.name,
                "members": [{
                    "assistantId": self.assistant_id.id_assistant,
                    "assistantDestinations": [
                        {
                            "type": "assistant",
                            "transferMode": rec.transfer_modes,
                            "assistantName": rec.assistant_id.name,
                            "description": rec.description,
                            "message": rec.message,
                        } for rec in self.assistant_ids
                    ],
                }]
            }
            for assistant_id in assistant_id_list:
                payload["members"].append({"assistantId": assistant_id})
            headers = {"Authorization": f"Bearer {bearer}",
                       "Content-Type": "application/json"}
            requests.request("PATCH", url, json=payload,
                             headers=headers)
            return res
