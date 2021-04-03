# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O @cybrosys(odoo@cybrosys.com)
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
#############################################################################

from odoo import http
from odoo.http import request


class PosProductCreation(http.Controller):

    @http.route('/create_product', type="json", auth="none")
    def create_product(self, category, name, price, product_reference, unit_measure, product_categories, **kwargs):
        product_category = ''
        if category == 'Consumable':
            product_category = 'consu'
        elif category == 'Service':
            product_category = 'service'
        elif category == 'Stockable':
            product_category = 'product'
        else:
            product_category = ''
        request.env['product.template'].sudo().create({
            'name': name,
            'type': product_category,
            'default_code': product_reference,
            'list_price': float(price),
            'uom_id': int(unit_measure),
            'uom_po_id': int(unit_measure),
            'categ_id': int(product_categories),
            'available_in_pos': True,
        })
