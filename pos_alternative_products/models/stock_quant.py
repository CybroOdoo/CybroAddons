# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
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
from odoo import api, models


class StockQuant(models.Model):
    """This class is used to compute the quantity and returns the product"""
    _name = 'stock.quant'
    _inherit = ['stock.quant', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        return [
            'product_id', 'available_quantity', 'quantity', 'location_id'
        ]

    def pos_stock_product(self, id):
        """It is used to check the available quantity of the selected product"""
        val = self.env['product.product'].browse(id)
        if val.qty_available <= 0:
            return 0
        else:
            return val

    def pos_alternative_product(self, alter_id, code):
        """Retrieve the corresponding product available in POS."""
        domain = [('product_tmpl_id', '=', alter_id)]
        if code:
            domain.append(('default_code', '=', code))

        product = self.env['product.product'].search(domain, limit=1)
        return self.product_in_pos(product.id) if product else 0

    def product_in_pos(self, product_id):
        """Check if the product is available in POS."""
        return product_id if self.env['product.product'].browse(
            product_id).available_in_pos else 0
