# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

class SolarionProduct(models.Model):
    _name = 'solarion.product'
    _description = 'Solarion Product'

    name = fields.Char(string='Name', required=True, help='Name of the product')
    efficiency = fields.Char(string='Efficiency', help='e.g., 47%')
    lifespan = fields.Char(string='Lifespan', help='e.g., 50 yrs')
    warranty = fields.Char(string='Warranty', help='e.g., Lifetime')
    description = fields.Html(string='Description', help='Description of the product')
    image = fields.Image(string='Image', max_width=1024, max_height=1024)
