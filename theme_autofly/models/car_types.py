# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class CarTypes(models.Model):
    """This model is used define car type fields and it's functionalities."""
    _name = "car.types"
    _description = "Website Car Type"

    name = fields.Char(help="Add your car type name.")
    image = fields.Image(help="Add your car type image.")
    product_count = fields.Integer(string='Products Count',
                                   compute='_compute_product_count',
                                   help="Used to show product in smart button.")

    def _compute_product_count(self):
        """Product count fetching based on car type."""
        for record in self:
            record.product_count = self.env['product.template'].search_count(
                [('car_type_id', '=', record.id)])

    def action_view_products(self):
        """Action to view corresponding products"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'view_mode': 'tree',
            'res_model': 'product.template',
            'domain': [('car_type_id', '=', self.id)],
            'context': "{'create': False}"
        }
