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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherit sale order model to validate unique product and location combinations."""
    _inherit = 'sale.order'

    @api.constrains('order_line')
    def _check_order_line(self):
        """Ensure that the same product cannot be added with the same location more than once."""
        for order in self:
            seen = set()
            for line in order.order_line:
                if line.product_id and line.line_location_id:
                    key = (line.product_id.id, line.line_location_id.id)
                    if key in seen:
                        raise ValidationError(
                            self.env._(
                                "You cannot add the same product '%(product)s' with the same location '%(location)s'.",
                                product=line.product_id.display_name,
                                location=line.line_location_id.name,
                            )
                        )
                    seen.add(key)
