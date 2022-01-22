# -*- coding: utf-8 -*-
# Copyright 2019 Noviat NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    gift_coupon_product_id = fields.Many2one(
        related='company_id.gift_coupon_product_id', string="Gift coupon")
