# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
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

################################################################################
from odoo import fields, models, api


class SaleConsignmentLine(models.Model):
    _name = "sale.consignment.line"
    _description = "Sale Consignment Line"

    @api.model
    def _settings_domain(self):
        product_domain = self.env[
            'ir.config_parameter'].get_param(
            'sale_consignment.consignment_product_only')
        return product_domain

    @api.depends('product_domain')
    def _product_domain(self):
        if self.env['ir.config_parameter'].get_param(
                'sale_consignment.consignment_product_only'):
            return [('is_consignment', '=', True)]
        else:
            return []

    product_id = fields.Many2one('product.product', string='Products',
                                 help="Product in the consignment order line",
                                 domain=lambda self: self._product_domain(),
                                 required=True)
    demand_quantity = fields.Integer(string='Demand Quantity',
                                     help="Demanded quantity of the product",
                                     required=True)
    done_quantity = fields.Integer(string='Done Quantity',
                                   help="Done quantity of the product")
    remaining_quantity = fields.Integer(string='Remaining Quantity',
                                        help="Quantity of remaining product",
                                        compute='_compute_remaining_quantity')
    price = fields.Float(string='Price', help="Price of the product")
    consignment_id = fields.Many2one('sale.consignment',
                                     string='Consignment ID',
                                     help="consignment ID for connect the"
                                          "consignment")
    condition_check_line = fields.Char()
    product_domain = fields.Boolean(
        default=lambda self: self._settings_domain())

    def _compute_remaining_quantity(self):
        for rec in self:
            rec.remaining_quantity = rec.demand_quantity - rec.done_quantity
