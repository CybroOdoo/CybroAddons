# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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


class ProductDataFeedColumns(models.Model):
    """Model for defining columns in a product data feed.

    This class represents the columns used in a product data feed. These columns
    define the structure of the data to be included in the feed, including
    various types such as text, model fields, values, and special types."""
    _name = 'product.data.feed.columns'
    _description = 'Product Data Feed Columns'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', help='Columns name')
    feed_id = fields.Many2one('product.data.feed',
                              string='Feed', help='Feed Name')
    type = fields.Selection(
        [('Text', 'Text'), ('Model Field', 'Model Field'),
         ('Value', 'Value'), ('Special', 'Special')],
        string='Type', help='Choose the type of the columns')
    value = fields.Char(string="Value", help='Enter the column value')
    value_id = fields.Many2one('ir.model.fields',
                               string="Value", help='Choose the column value',
                               )
    field_value_id = fields.Many2one('field.column.value',
                                     string="Value",
                                     help='Choose the column value')
    data_feed_columns_id = fields.Many2one('product.data.feed',
                                           string='Data Columns',
                                           help='Data columns inverse field')
    special_type = fields.Selection(
        [('product_price', 'Product Price'),
         ('disc_price', 'Discounted Price'),
         ('price_currency', 'Price Currency'),
         ('product_availability', 'Product Availability'),
         ('qty', 'Qty in Stock'),
         ('price_tax', 'Product Price(with Taxes)'),
         ('price_without_tax', 'Product Price(without Taxes)')],
        string='Special Type', help='Choose the special type')
