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


class FieldColumnValue(models.Model):
    """Model for storing field column values.

    This class represents field column values used in a product data feed.
    It is used to define the mapping of column names to their corresponding
     values.
   """
    _name = 'field.column.value'
    _description = 'Field Column Value'
    _rec_name = 'value'

    feed_id = fields.Many2one('product.data.feed',
                              string='Feed Name', help='Feed Name')
    column_name = fields.Char(string='Column Name',
                              help='Enter the column name.')
    value = fields.Char(string='Value', help='Value of the column name.')
