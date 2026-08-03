# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Arjun P P (odoo@cybrosys.com)
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
###############################################################################
import base64
import io
import json

import qrcode
import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ConfigurationManager(models.Model):
    """A new model is to be created for configuring the API settings
    required to connect to WhatsApp."""

    _name = "configuration.manager"
    _description = "Configuration Manager"
    _rec_name = "instance"

    instance = fields.Char(string="Instance", required=True, help="Give instance for whatsapp api")
    token = fields.Char(string="Token", required=True, help="Give token for whatsapp api")
    config_id = fields.Many2one("pos.config",
        string="Point of Sale",
        required=True,
        help="Give Point of Sale for whatsapp api",)
    state = fields.Selection(selection=[("draft", "Draft"), ("verified", "Verified")],
        default="draft",
        string="state",
        help="State for connection",)

    def action_authenticate(self):
        """Opens a wizard for scanning QR code,
        After scanning number get active status."""
        url = f"https://api.ultramsg.com/{self.instance}/instance/status"
        querystring = {
            "token": self.token,
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        try:
            req = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
        except requests.RequestException as e:
            raise ValidationError(_("Connection to WhatsApp API failed: %s") % str(e))

        if req.status_code != 200:
            raise ValidationError(_("Please provide valid token"))
        if req.text == "Client not found.":
            return self.display_notification(
                "danger", "Please check the field values"
            )
        try:
            res_json = req.json()
        except (ValueError, TypeError):
            res_json = {}

        substatus = (
            res_json
            .get("status", {})
            .get("accountStatus", {})
            .get("substatus")
        )
        if substatus == "normal":
            self.state = "draft"
            qr_code_data = self.get_qr_code()
            if qr_code_data:
                return self.open_authenticate_wizard(qr_code_data)
        if substatus == "connected":
            self.state = "verified"
            return self.display_notification("success", "Already connected")

    def get_qr_code(self):
        """Retrieve the QR code from the Ultramsg API."""
        url = f"https://api.ultramsg.com/{self.instance}/instance/qrCode"
        querystring = {
            "token": self.token,
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            if response.status_code == 200:
                qr_code_data = response.text
                return qr_code_data
        except requests.RequestException:
            pass
        return None

    def display_notification(self, message_type, message):
        """Got connected message"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": message_type,
                "sticky": False,
            },
        }

    def open_authenticate_wizard(self, qr_code_data):
        """Opens QR code scanning wizard"""
        try:
            decoded_data = json.loads(qr_code_data)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, treat the raw response text as the QR code string directly
            decoded_data = {"qrCode": qr_code_data}

        if not isinstance(decoded_data, dict) or "qrCode" not in decoded_data:
            message = ""
            if isinstance(decoded_data, dict):
                message = decoded_data.get("message") or decoded_data.get("error") or str(decoded_data)
            else:
                message = str(decoded_data)
            return self.display_notification(
                "danger", f"Could not retrieve QR code: {message}"
            )

        qr_code_string = decoded_data["qrCode"]
        img = qrcode.make(qr_code_string)
        result = io.BytesIO()
        img.save(result, format="PNG")
        result.seek(0)
        image_result = base64.b64encode(result.read())
        return {
            "type": "ir.actions.act_window",
            "res_model": "whatsapp.authenticate",
            "name": "WhatsApp Connect",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_qrcode": image_result,
                "default_configuration_manager_id": self.id,
            },
        }
