# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WhatsappAuthenticate(models.TransientModel):
    """Create a new model"""
    _name = 'whatsapp.authenticate'
    _description = 'Whatsapp Authentication Wizard'

    qrcode = fields.Binary(attachment=False, string="Qr Code",
                           help="QR code for scanning")
    configuration_manager_id = fields.Many2one("configuration.manager",
                                               string="Configuration Manager",
                                               help="Configuration manager"
                                                    "details")

    @api.constrains('config_manager_id')
    def _check_active(self):
        """check the scanned number is active or not."""
        url = "https://api.apichat.io/v1/status"
        headers = {
            "client-id": self.configuration_manager_id.instance,
            "token": self.configuration_manager_id.token
        }
        req = requests.get(url, headers=headers, timeout=10)
        if 'is_connected' in req.json().keys():
            if req.json()['is_connected']:
                self.configuration_manager_id.state = "verified"
        else:
            raise ValidationError(
                _("Please scan and connect your whatsapp web"))
        if self.configuration_manager_id.state != "verified":
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Check The Connection',
                    'type': 'danger',
                    'sticky': False,
                }
            }
