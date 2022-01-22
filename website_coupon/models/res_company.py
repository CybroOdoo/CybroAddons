# -*- coding: utf-8 -*-
# Copyright 2019 Noviat NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    gift_coupon_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Gift coupon",
        default=lambda self: self.env['product.product'].search(
            [('default_code', '=', 'gift_coupon')], limit=1),
    )
