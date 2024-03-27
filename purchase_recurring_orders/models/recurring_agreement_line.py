# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayana KP (odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.addons.base.models.decimal_precision import dp


class RecurringAgreementLine(models.Model):
    """Model generating purchase recurring agreement line"""
    _name = 'recurring.agreement.line'
    _description = 'Recurring Agreement Line'

    active_chk = fields.Boolean(
        string='Active', default=True,
        help='Unchecking this field, this quota is not generated')
    recurring_agreement_id = fields.Many2one(
        'purchase.recurring.agreement',
        string='Agreement Reference',
        help="The Corresponding Purchase Order Agreement",
        ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict',
                                 required=True)
    uom_id = fields.Many2one(related='product_id.product_tmpl_id.uom_id',
                             help="UOM of the product", string="Uom")

    name = fields.Char(
        related="product_id.name", string='Description',
        help="Description of the Product")
    additional_description = fields.Char(
        string='Description', size=30,
        help='Additional description that will be added to the product '
             'description on orders.')
    quantity = fields.Float(
        string='Quantity', required=True, help='Quantity of the Product',
        default=1.0)
    ordering_interval = fields.Integer(
        string='Interval', required=True, default=1,
        help="Interval in time units for making an order of this product")
    ordering_unit = fields.Selection(
        selection=[('days', 'Days'),
                   ('weeks', 'Weeks'),
                   ('months', 'Months'),
                   ('years', 'Years')],
        string='Interval Unit', required=True,
        help="It indicated the Recurring Time Unit", default='months')
    last_order_date = fields.Datetime(
        string='Last Order', help='Date of the last Purchase order generated')
    specific_price = fields.Float(
        string='Specific Price',
        digits_compute=dp.get_precision('Purchase Price'),
        help='Specific price for this product. Keep empty to use the list '
             'price while generating order')
    list_price = fields.Float(
        related='product_id.list_price', string="List Price", readonly=True,
        help='Price of product in purchase order lines')

    _sql_constraints = [
        ('line_qty_zero', 'CHECK (quantity > 0)',
         'All product quantities must be greater than 0.\n'),
        ('line_interval_zero', 'CHECK (ordering_interval > 0)',
         'All ordering intervals must be greater than 0.\n'),
    ]

    @api.onchange('product_id')
    def onchange_product_id(self, product_id=False):
        """For getting product name"""
        result = {}
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product:
                result['value'] = {'name': product['name']}
        return result
