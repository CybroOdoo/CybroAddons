# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P(odoo@cybrosys.com)
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

################################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create_from_ui(self, payload):
        """ Create or modify a Product from the point of sale ui.
            Product contains the Product's fields. """

        base64_content = payload.get('image_1920', False)
        image = base64_content.split(',', 1)[-1]
        if payload.get('pos_categ_ids') and isinstance(
                payload.get('pos_categ_ids'), str):
            pos_categ_ids = [int(item) for item in
                             payload.get('pos_categ_ids').split(',')]
        else:
            pos_categ_ids = payload.get('pos_categ_ids')
        product_id = payload.get('id')
        values = {
            'name': payload.get('name'),
            'image_1920': image,
            'standard_price': float(
                payload.get('standard_price')) if payload.get(
                'standard_price') else 0,
            'lst_price': float(payload.get('lst_price')) if payload.get(
                'lst_price') else 0,
            'pos_categ_ids': pos_categ_ids if payload.get(
                'pos_categ_ids') and payload.get(
                'pos_categ_ids') != '0' else False,
            'default_code': payload.get('default_code'),
            'available_in_pos': True
        }
        if payload.get('image_1920') == "":
            del values['image_1920']
        if product_id:  # Modifying existing product
            self.browse(product_id).write(values)
        else:
            product = self.create(values)
            product_id = product.id
        return product_id
