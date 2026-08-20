# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class StockLocation(models.Model):
    """Routes material to the sub-area providing the storage class it requires."""
    _inherit = 'stock.location'

    def _get_putaway_strategy(self, product, *args, **kwargs):
        """Resolve the product's storage class into a physical sub-area."""
        required = product.storage_category_id
        if required and self.storage_category_id != required:
            area = self.search([
                ('id', 'child_of', self.id),
                ('usage', '=', 'internal'),
                ('storage_category_id', '=', required.id),
            ], limit=1, order='complete_name')
            if area:
                return super(StockLocation, area)._get_putaway_strategy(
                    product, *args, **kwargs) or area
        return super()._get_putaway_strategy(product, *args, **kwargs)

    def _pharma_storage_categories(self):
        """Walk up location_id accumulating storage_category_id."""
        self.ensure_one()
        categories = self.env['stock.storage.category']
        location = self
        while location:
            categories |= location.storage_category_id
            location = location.location_id
        return categories
