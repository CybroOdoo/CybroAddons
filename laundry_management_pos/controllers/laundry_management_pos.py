# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import http
from odoo.http import request


class PosProductCreation(http.Controller):
    """Class PosProductCreation is used to create a product from the POS
     Screen"""
    @http.route('/create_product', type="json", auth="none")
    def create_product(self, category, name, price, product_reference,
                       unit_measure, product_categories):
        """Used for creating product from the point of sale view
        that easily create a new product from the point of sale"""
        categories = {
            'Consumable': 'consu',
            'Service': 'service',
            'Storable': 'product'
        }
        request.env['product.template'].sudo().create({
            'name': name,
            'detailed_type': categories.get(category, ''),
            'default_code': product_reference,
            'list_price': float(price),
            'uom_id': int(unit_measure),
            'uom_po_id': int(unit_measure),
            'categ_id': int(product_categories),
            'available_in_pos': True,
        })
