# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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


class ResConfigSettings(models.TransientModel):
    """ Inherited this module is to add fields for WhatsApp's
        message-sending authentication """
    _inherit = "res.config.settings"

    api_key = fields.Char(string="API Key",
                          config_parameter='infobip_whatsapp_integration.'
                                           'api_key',
                          help="Enter your API Key for Infobip WhatsApp"
                               " integration.")
    base_url = fields.Char(string="Base URL",
                           config_parameter='infobip_whatsapp_integration.'
                                            'base_url',
                           help="Enter the base URL for Infobip WhatsApp "
                                "integration.")
    infobip_whatsapp = fields.Char(string="Infobip Whatsapp Number",
                                   config_parameter='infobip_whatsapp_integration'
                                                    '.infobip_whatsapp',
                                   help="Enter the Infobip WhatsApp number "
                                        "for integration.")
