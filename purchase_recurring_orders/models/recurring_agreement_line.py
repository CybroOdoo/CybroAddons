# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ruksana P (odoo@cybrosys.com)
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
from odoo.addons.base.models.decimal_precision import dp


class RecurringAgreementLine(models.Model):
    """Model generating purchase recurring agreement line"""
    _name = 'recurring.agreement.line'
    _description = 'Recurring Agreement Records'

    is_active = fields.Boolean(string='Active', default=True,
                               help='Unchecking this field, this quotation for'
                                    'this product is not generated')
    recurring_agreement_id = fields.Many2one('purchase.recurring.agreement',
                                             string='Agreement Reference',
                                             ondelete='cascade',
                                             help="The Corresponding purchase"
                                                  " order agreement")
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict', required=True)
    uom_id = fields.Many2one(related='product_id.product_tmpl_id.uom_id',
                             help="UOM of the product", string="Uom")
    additional_description = fields.Char(string='Description', size=30,
                                         help='Additional description that will'
                                              ' be added to the product '
                                              'description on orders.')
    quantity = fields.Float(string='Quantity', required=True,
                            help='Quantity of the product', default=1.0)
    ordering_interval = fields.Integer(string='Interval', required=True,
                                       help="Interval in time units for making"
                                            " an order of this product",
                                       default=1)
    ordering_unit = fields.Selection([('days', 'Days'), ('weeks', 'Weeks'),
                                      ('months', 'Months'), ('years', 'Years')],
                                     string='Interval Unit', required=True,
                                     help="It indicated the recurring time unit"
                                     , default='months')
    last_order_date = fields.Datetime(help='Date of the last Purchase order '
                                           'generated', string='Last Order')
    specific_price = fields.Float(
        string='Specific Price',
        digits_compute=dp.get_precision('Purchase Price'),
        help='Specific price for this product. Keep empty to use the list '
             'price while generating order')
    list_price = fields.Float(related='product_id.list_price', readonly=True,
                              string="List Price", help='Unit price of product')

    _sql_constraints = [
        ('line_qty_zero', 'CHECK (quantity > 0)',
         'All product quantities must be greater than 0.\n'),
        ('line_interval_zero', 'CHECK (ordering_interval > 0)',
         'All ordering intervals must be greater than 0.\n'),
    ]
