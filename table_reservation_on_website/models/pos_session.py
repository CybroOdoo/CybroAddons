# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class PosSession(models.Model):
    """inherited pos session to load the product product"""
    _inherit = 'pos.session'

    def _get_pos_ui_product_product(self, params):
        """load product to pos"""
        result = super()._get_pos_ui_product_product(params)
        product = self.env.ref('table_reservation_on_website'
                               '.product_product_table_booking')

        data = product.read(fields=params['search_params']['fields'])
        append_data = data[0]
        append_data['categ'] = {'id': product.categ_id.id,
                                'name': product.categ_id.name,
                                'parent_id': product.categ_id.parent_id.id,
                                'parent': None}
        result.append(append_data)
        return result
