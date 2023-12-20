# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class CarBrand(models.Model):
    """This model is used define Brand Model fields and functionalities."""
    _name = "car.brand"
    _description = "Website Car Brand"

    name = fields.Char(string="Name", help="Add your brand name.")
    image = fields.Image(string="Image", help="Add your brand image.")

    @api.model
    def get_brands(self):
        """Rpc function returning car details."""
        brands = self.env['car.brand'].sudo().search([])
        car_type = self.env['car.types'].sudo().search([])
        car_name = []
        car_id = []
        for rec in brands:
            car_name.append(rec.name)
            car_id.append(rec.id)
        value = {
            'car_name': car_name,
            'car_id': car_id
        }
        type_name = []
        type_id = []
        for record in car_type:
            type_name.append(record.name)
            type_id.append(record.id)
        value1 = {
            'car_type': type_name,
            'type_id': type_id
        }
        return value, value1
