# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Added fields in settings."""
    _inherit = 'res.config.settings'

    enable_whatsapp = fields.Boolean(string='Enable Whatsapp in POS',
                                     config_parameter='pos_invoice_in_whatsapp.enable_whatsapp',
                                     help='Enable this feature to send'
                                          ' messages to the corresponding'
                                          ' customer')
    auth_token = fields.Char(string="Auth Token", check_company=True,
                             config_parameter='pos_invoice_in_whatsapp.auth_token',
                             help="Authorization Token of Whatsapp Cloud "
                                  "API", required=True)

    whatsapp_no = fields.Char(string="Phone number ID", check_company=True,
                              help="Phone Number ID of Whatsapp Cloud API",
                              config_parameter='pos_invoice_in_whatsapp.whatsapp_no',
                              required=True)
    whatsapp_business = fields.Char(help="Business ID of Whatsapp Cloud API",
                                    string="Whatsapp Business Account ID",
                                    config_parameter='pos_invoice_in_whatsapp.whatsapp_business',
                                    required=True)
