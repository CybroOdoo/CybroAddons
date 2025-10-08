# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class RentalProductCategory(models.Model):
    """Created the class for creating the model rental product category"""
    _name = 'rental.product.category'
    _description = 'Rental Product Category'

    name = fields.Char(string='Name', required=True,
                       help='Name of product category')

    def action_view_rental_products(self):
        """Showing the products under the rental category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Products',
            'view_mode': 'tree',
            'res_model': 'product.product',
            'domain': [('category_id', '=', self.id)],
            'context': "{'create': False}"
        }
