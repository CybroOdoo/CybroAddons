###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""Price history tracking model for product standard prices."""
from odoo import fields, models


class PriceHistory(models.Model):
    """
    Keep track of the price of products standard prices as they are changed.
    """
    _name = 'price.history'
    _description = 'Products Price History'
    _order = 'datetime desc'

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
        help="Choose your company",
    )
    product_id = fields.Many2one(
        'product.product',
        ondelete='cascade',
        required=True,
        help="Choose product",
    )
    datetime = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        help="Choose the date",
    )
    cost = fields.Float(
        digits='Product Price',
        help="Product Price",
    )
