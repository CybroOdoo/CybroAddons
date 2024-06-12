# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


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

    def action_save(self):
        """ Action for Save Button which will check Authentication"""
        self.configuration_manager_id.action_authenticate()
