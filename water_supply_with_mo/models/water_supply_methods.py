# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class WaterSupplyMethods(models.Model):
    """Creating water supply methods. """
    _name = 'water.supply.methods'
    _description = 'Water Supply Methods'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'supply_name'

    code = fields.Char(string='Internal Code', help='Code of the supply'
                                                    ' method')
    supply_name = fields.Char(string='Supply Name', help='Supply name')
    created_product_id = fields.Many2one('product.product',
                                         string='Product Created',
                                         help="Product created when method "
                                              "is created")

    @api.model_create_multi
    def create(self, vals_list):
        """Creating corresponding product for each method."""
        records = super(WaterSupplyMethods, self).create(vals_list)
        for record in records:
            product_records = {
                'name': record.supply_name,
                'detailed_type': 'product'
            }
            created_product = self.env['product.product'].create(
                product_records).id
            record.created_product_id = created_product
        return records
