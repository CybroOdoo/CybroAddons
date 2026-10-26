# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com/>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com/>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited res.config.settings class to add fields and functions to get
    and set values in purchase settings form"""
    _inherit = 'res.config.settings'

    is_auto_generate = fields.Boolean(
        string='Auto Generate',
        help="Enable automatic generation of lot and serial numbers on receipts",
        config_parameter="auto_generate_lot_number.is_auto_generate"
    )
    serial_number_type = fields.Selection(
        [('global', 'Global'), ('product', 'Product Wise')],
        default='global',
        string='Serial/Lot Number',
        help="Generate lot and serial numbers product-wise or globally",
        config_parameter="auto_generate_lot_number.serial_number_type"
    )
    prefix = fields.Char(
        string='Prefix',
        help="Prefix value used for generating the sequence",
        config_parameter="auto_generate_lot_number.prefix"
    )
    digits = fields.Integer(
        string='Digits',
        help="Used to set number of digits contained in a sequence",
        config_parameter="auto_generate_lot_number.digits"
    )

    def set_values(self):
        """Set parameter values and persist company check_auto_generate field"""
        super().set_values()
        self.env.company.check_auto_generate = bool(self.is_auto_generate)

    def get_values(self):
        """Retrieve stored configuration parameters for auto generate settings"""
        res = super().get_values()
        res.update(
            is_auto_generate=self.env['ir.config_parameter'].sudo().get_bool(
                'auto_generate_lot_number.is_auto_generate'
            ),
        )
        return res