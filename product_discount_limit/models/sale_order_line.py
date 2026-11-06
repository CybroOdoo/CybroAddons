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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, exceptions, models


class SaleOrderLine(models.Model):
    """Inherit sale.order.line to check the discount limit allowed
    for products and product categories"""
    _inherit = 'sale.order.line'

    @api.onchange('discount')
    def _onchange_discount(self):
        """Check the discount limit allowed for the product and its category"""
        if not self.env.user.allow_discount:
            desc_limit = self.product_id.product_tmpl_id.desc_limit or \
                         self.product_id.categ_id.desc_limit
            if desc_limit and self.discount > desc_limit:
                limit_type = (
                    'product'
                    if self.product_id.product_tmpl_id.desc_limit
                    else 'category'
                )
                raise exceptions.UserError(
                    self.env._(
                        'You are not allowed to apply a discount of more than '
                        '%(desc_limit)s%% on this %(limit_type)s. '
                        'Please contact your administrator.',
                        desc_limit=desc_limit,
                        limit_type=limit_type,
                    )
                )
