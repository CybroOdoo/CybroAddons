# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import fields, models


class SaleOrder(models.Model):
    """Inherit sale order model to add customer feedback fields."""
    _inherit = 'sale.order'

    is_textile_sale_order = fields.Boolean(
        string="Is Textile Sale Order",
        help="To check its created from textile module",
        copy=False,
    )
    comment = fields.Char(
        string='Comment',
        readonly=True,
        help='The comment provided by the customer.',
    )
    rating = fields.Selection([
        ('0', 'Too Bad'),
        ('1', 'Poor'),
        ('2', 'Average Quality'),
        ('3', 'Nice'),
        ('4', 'Good'),
    ], string='Rating', readonly=True,
        help='The rating provided by the customer.',
    )

    # NOTE: _action_confirm override removed.
    # The /customer/review/session controller now writes rating and comment
    # directly onto the active sale order as soon as the customer interacts
    # with the feedback widget — before they click Pay. No session storage
    # or _action_confirm hook is needed.