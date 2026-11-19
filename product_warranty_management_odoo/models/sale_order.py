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
from odoo import fields, models


class SaleOrder(models.Model):
    """Flag confirmed orders that contain warranty products."""
    _inherit = 'sale.order'

    is_warranty_check = fields.Boolean(
        string='Has Warranty', copy=False,
        help='Set on confirmation when the order contains at least one '
             'product with a warranty.')

    def action_confirm(self):
        """Mark each confirmed order that contains warranty products."""
        res = super().action_confirm()
        for order in self:
            order.is_warranty_check = any(
                order.order_line.product_id.mapped('is_warranty_available'))
        return res

    def action_open_warranty_details(self):
        """Open the warranty lines of this order with their expiry dates."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Warranty Details'),
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('product_warranty_management_odoo.'
                              'sale_order_line_view_list_warranty').id,
                 'list'),
                (self.env.ref('product_warranty_management_odoo.'
                              'sale_order_line_view_form_warranty').id,
                 'form'),
            ],
            'domain': [('order_id', '=', self.id),
                       ('is_warranty_available', '=', True)],
            'context': {'create': False},
        }
