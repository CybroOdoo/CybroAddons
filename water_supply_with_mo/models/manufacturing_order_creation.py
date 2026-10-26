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


class ManufacturingOrderCreation(models.Model):
    """Model to create and manage manufacturing orders from water supply
    requests."""
    _name = 'manufacturing.order.creation'
    _description = 'Manufacturing Order Creation'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product',
                                 string='Product', help='Name of the product')
    quantity = fields.Integer(string='Quantity',
                              help='Quantity of the product')
    uom_id = fields.Many2one('uom.uom', string='UoM',
                             help='Unit of measure of the product')
    bom_id = fields.Many2one('mrp.bom',
                             domain="[('product_id','=', product_id)]",
                             string='Bill of Material',
                             help='Bill of material of the product.')
    mrp_id = fields.Many2one('mrp.production',
                             string='Manufacturing Order',
                             help='Manufacturing order of the product')
    is_mo = fields.Boolean(string='Display MO Button', default=True,
                           help='If false, the manufacturing order button '
                                'will be hidden.')
    supply_request_id = fields.Many2one('water.supply.request',
                                        string='Supply Request',
                                        help="Corresponding water supply "
                                             "request")

    def action_creating_mo(self):
        """Display manufacturing order for the product with default values.
        The form view will display default values for the specified fields
        based on the attributes of the current instance.
        The view will be opened in the current window."""
        res = {
            'name': 'mrp.production',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'mrp.mrp_production_form_view').id,
            'target': 'current',
            'context': {
                'default_product_id': self.product_id.id,
                'default_product_qty': self.quantity,
                'default_supply_id': self.supply_request_id.id,
                'default_manufacturing_order_id': self.id
            },
        }
        return res
