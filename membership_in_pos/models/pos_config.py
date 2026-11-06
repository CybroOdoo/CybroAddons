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
from odoo import models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _get_special_products(self):
        res = super()._get_special_products()
        product_id_str = self.env['ir.config_parameter'].sudo().get_str('pos_membership_product_id')
        if product_id_str and product_id_str != 'False':
            try:
                product_id = int(product_id_str)
                membership_product = self.env['product.product'].browse(product_id)
                res |= membership_product
            except ValueError:
                pass
        return res
