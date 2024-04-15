# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
#
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    """inherit model product.product"""
    _inherit = 'product.product'

    def action_create_rfq(self):
        """
        method to create rfq from server action
        return product.rfq wizard to configure rfq
        """
        product_rfq = self.env['product.rfq'].create({
            'rfq_line_ids':  [(0, 0, {
                'product_id': product.id,
                'product_qty': 1.0,
                'price_unit': product.standard_price,
            }) for product in self]
        })
        return {
            'view_mode': 'form',
            'res_model': 'product.rfq',
            'res_id': product_rfq.id,
            'view_id': self.env.ref(
                'quick_rfq.product_rfq_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
