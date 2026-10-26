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


class MrpProduction(models.Model):
    """ This class adds additional fields and overrides the 'create' method
     for specific functionality."""
    _inherit = 'mrp.production'

    manufacturing_order_id = fields.Many2one('manufacturing.order.creation',
                                             string='Manufacturing Order Line',
                                             help='Linked manufacturing order creation line')
    supply_id = fields.Many2one('water.supply.request',
                                string='Water Supply Request',
                                help='Linked water supply request')

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new Manufacturing Production."""
        records = super().create(vals_list)
        default_mo_context_id = self.env.context.get(
            'default_manufacturing_order_id')
        default_manufacturing_order = self.env[
            'manufacturing.order.creation'].browse(default_mo_context_id)
        for res in records:
            if default_manufacturing_order:
                default_manufacturing_order.mrp_id = res
                default_manufacturing_order.bom_id = res.bom_id
                default_manufacturing_order.is_mo = False
        return records
