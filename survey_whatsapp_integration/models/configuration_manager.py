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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ConfigurationManager(models.Model):
    """Create new model"""
    _name = "configuration.manager"
    _description = "Configuration Manager"
    _rec_name = 'instance'

    instance = fields.Char(string="Instance", required=True,
                           help="Give instance for whatsapp api")
    token = fields.Char(string="Token", required=True,
                        help="Give token for whatsapp api")
    state = fields.Selection(
        selection=[('draft', 'Not Verified'),
                   ('verified', 'Verified')],
        default='draft', string="Status",
        help="State for connection", readonly=True)

    def action_authenticate(self):
        """ Opens a wizard for scanning QR code,
        After scanning number get active status."""
        url = "https://api.apichat.io/v1/status"
        headers = {
            "client-id": self.instance,
            "token": self.token
        }
        req = requests.get(url, headers=headers, timeout=10)
        if req.status_code != 200:
            raise ValidationError(_("Please provide valid token"))
        if req.text == 'Client not found.':
            return self.display_notification('danger',
                                             'Please check the field values')
        if 'qr' in req.json().keys():
            self.state = "draft"
            new_data = req.json()['qr'].replace('data:image/png;base64,', '')
            return self.open_authenticate_wizard(new_data)
        if req.json()['is_connected']:
            self.state = "verified"
            return self.display_notification('success',
                                             'Already connected')

    def display_notification(self, message_type, message):
        """ Got connected message"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': message_type,
                'sticky': False,
            }
        }

    def open_authenticate_wizard(self, qrcode):
        """Opens QR code scanning wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.authenticate',
            'name': 'WhatsApp Connect',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_qrcode': qrcode,
                'default_config_manager_id': self.id,
            }
        }
