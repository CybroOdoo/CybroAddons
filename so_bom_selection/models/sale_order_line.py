# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Inherited model 'sale.order.line' and added required fields"""
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='Bill of Material',
                             help="Bill of materials for the product")
    product_template_id = fields.Many2one(related="product_id.product_tmpl_id",
                                          string="Template Id of Selected"
                                                 " Product",
                                          help="Template id of the "
                                               "selected product")

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """ Override the function to set the newly created MO id to the
         corresponding stock move of the order line."""
        result = super(SaleOrderLine, self)._action_launch_stock_rule(
            previous_product_uom_qty)
        for rec in self:
            if rec.bom_id:
                mo = self.env['mrp.production'].search(
                    [('sale_line_id', '=', rec.id)])
                if mo:
                    move = self.env['stock.move'].search(
                        [('sale_line_id', '=', rec.id)])
                    if not move.created_production_id:
                        move.created_production_id = mo.id
        return result
