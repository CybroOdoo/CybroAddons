# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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
################################################################################
from odoo import models


class SaleOrder(models.Model):
    """
    Inherits the sale.order model to extend its functionality.
    """
    _inherit = 'sale.order'

    def _cart_add(self, product_id, quantity=1.0, *, uom_id=None, **kwargs):
        """
        Odoo 20 cart add override: ensures uom_id is passed as integer to super.
        Does not fall back to session-wide UOM so different products keep their own UOM.
        """
        if isinstance(uom_id, models.Model):
            uom_id = uom_id.id
        elif uom_id:
            try:
                uom_id = int(uom_id)
            except (ValueError, TypeError):
                uom_id = None
        return super()._cart_add(product_id, quantity=quantity, uom_id=uom_id, **kwargs)

    def _cart_find_product_line(self, product_id, uom_id=None, **kwargs):
        """
        Find the cart line matching the given parameters.
        Filter by UOM to allow different UOM variants of the same product
        to be added as separate lines.
        """
        self.ensure_one()
        if isinstance(uom_id, models.Model):
            uom_id = uom_id.id
        elif uom_id:
            try:
                uom_id = int(uom_id)
            except (ValueError, TypeError):
                uom_id = None
        return super()._cart_find_product_line(product_id, uom_id=uom_id, **kwargs)
