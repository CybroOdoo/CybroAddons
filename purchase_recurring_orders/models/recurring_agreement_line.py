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
        help="The corresponding purchase agreement",
        ondelete='cascade')
    product_id = fields.Many2one('product.product',
                                 ondelete='restrict',
                                 help="Products",
                                 required=True)
    uom_id = fields.Many2one(related='product_id.product_tmpl_id.uom_id',
                             help="Unit of measure of the product", string="UoM")

    name = fields.Char(
        related="product_id.name", string='Description',
        help="Description of the Product")
    additional_description = fields.Char(
        string='Description', size=30,
        help='Additional description that will be added to the product '
             'description on orders.')
    quantity = fields.Float(
        required=True, help='Quantity of the product',
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
        help="Indicates the recurring time unit", default='months')
    last_order_date = fields.Datetime(
        string='Last Order', help='Date of the last purchase order generated')
    specific_price = fields.Float(
        digits='Product Price',
        help='Specific price for this product. Keep empty to use the list '
             'price while generating the order')
    list_price = fields.Float(
        related='product_id.list_price', string="List Price", readonly=True,
        help='Price of product in purchase order lines')

    _sql_constraints = [
        ('line_qty_zero', 'CHECK (quantity > 0)',
         'All product quantities must be greater than 0.\n'),
        ('line_interval_zero', 'CHECK (ordering_interval > 0)',
         'All ordering intervals must be greater than 0.\n'),
    ]
