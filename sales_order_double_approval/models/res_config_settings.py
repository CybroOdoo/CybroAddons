# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    """ Inheriting the settings to add custom fields """
    _inherit = 'res.config.settings'

    so_min_amount_currency_id = fields.Many2one(
        'res.currency',
        string="Threshold Currency",
        config_parameter="sales_order_double_approval.so_min_amount_currency_id",
        default=lambda self: self.env.ref('base.main_company').currency_id,
    )
    so_min_amount = fields.Monetary(
        string="Minimum Amount",
        currency_field='so_min_amount_currency_id',
        help="Specify the minimum amount that triggers the double validation "
             "for sale orders. Sale orders exceeding this amount will require "
             "approval by a sales manager."
    )

    @api.model
    def get_values(self):
        """Load the monetary threshold from the configuration parameters."""
        res = super().get_values()
        res['so_min_amount'] = self.env['ir.config_parameter'].sudo().get_float(
            "sales_order_double_approval.so_min_amount")
        return res

    def set_values(self):
        """Save the monetary threshold in the configuration parameters."""
        self.env['ir.config_parameter'].sudo().set_float(
            "sales_order_double_approval.so_min_amount",
            self.so_min_amount)
        super().set_values()
