# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Farhana Jahan PT (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """ Inherit the 'sale_order' model and add a smart tab along with
     a Many 2 many field."""
    _inherit = 'sale.order'

    mrp_count = fields.Integer(compute='_compute_mrp_count',
                               string="MRP Count",
                               help="Get total count of mrp order")
    mrp_production = fields.Many2many("mrp.production",
                                      string="MRP Orders",
                                      help="Get MRP order in sale order")

    def _compute_mrp_count(self):
        """Compute function for getting total count of manufacturing order
        related to the corresponding sale"""
        for record in self:
            record.mrp_count = self.env['mrp.production'].search_count(
                [('sale_order_id', '=', record.id)])

    def action_mrp_order(self):
        """Button action for generating Manufacturing Orders while
        selecting Sale Orders."""
        for order in self:
            if order.mrp_production:
                raise ValidationError(
                    "The sale order has already a manufacturing order.!")
            if order.state == "draft":
                for line in order.order_line:
                    if not line.product_id.qty_available:
                        self.env['mrp.production'].create({
                            'product_qty': line.product_uom_qty,
                            'product_id': line.product_id.id,
                            'sale_order_id': order.id,
                        })
                order.mrp_production = self.env['mrp.production'].search(
                    [('sale_order_id', '=', order.id)])
            else:
                raise ValidationError("Choose the draft sale order.!")

    def get_mrp(self):
        """smart button action for getting manufacturing orders of
        corresponding sale"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Order',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'domain': [('sale_order_id', '=', self.id)],
            'context': "{'create': False}"
        }
