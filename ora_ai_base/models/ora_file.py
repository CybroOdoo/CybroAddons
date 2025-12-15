# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
from odoo import api, fields, models


class OraFile(models.Model):
    """Used to store custom files."""
    _name = "ora.file"
    _description = "Ora File"

    name = fields.Char(string="Name", required=True,
                       help="A descriptive name for the file.")
    file = fields.Binary(string="File", required=True,
                         help="The actual binary file to be stored.")
    id_file = fields.Char(string="File id", readonly=True,
                          help="The unique identifier of the file,")

    @api.model_create_multi
    def create(self, vals):
        """Create a new OraFile record and upload the file to the
         VAPI platform."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        res = super().create(vals)
        decoded_data = base64.b64decode(res.file)
        url = "https://api.vapi.ai/file"
        files = {
            "file": (res.name, decoded_data, "application/pdf")
        }
        headers = {
            "Authorization": f"Bearer {bearer}"
        }
        response = requests.post(url, files=files, headers=headers)
        json_response = response.json()
        res.write({'id_file': json_response.get('id')})
        return res

    def unlink(self):
        """Delete OraFile record and remove the associated file from
         the VAPI platform."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        for rec in self:
            url = f"https://api.vapi.ai/file/{rec.id_file}"
            headers = {
                "Authorization": f"Bearer {bearer}"}
            requests.request("DELETE", url, headers=headers)
        res = super().unlink()
        return res

    def write(self, vals):
        """Update the OraFile record and propagate changes to
        the VAPI platform."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        res = super().write(vals)
        if self.id_file:
            url = f"https://api.vapi.ai/file/{self.id_file}"
            payload = {"name": self.name}
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json"
            }
            requests.request("PATCH", url, json=payload,
                             headers=headers)
        return res
