# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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


class FreightRoutes(models.Model):
    """Creating the routes for the freight"""
    _name = 'freight.routes'
    _description = 'Freight Routes'

    name = fields.Char(string='Name', required=True, help='Name of the route')
    active = fields.Boolean(string='Active', default=True,
                            help='For activating the route')
    land_sale = fields.Float(string='Land Sale Price', required=True,
                             help='Sale price for land')
    air_sale = fields.Float(string='Air Sale Price', required=True,
                            help='Sale price for Air')
    water_sale = fields.Float(string='Water Sale Price', required=True,
                              help='Sale price for Air')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
