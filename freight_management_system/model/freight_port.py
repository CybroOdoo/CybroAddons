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


class FreightPort(models.Model):
    """Creating different port location for managing freight"""
    _name = 'freight.port'
    _description = 'Freight Port'

    name = fields.Char(string='Name', help='Name for the port')
    code = fields.Char(string='Code', help='Specify a code for freight')
    state_id = fields.Many2one('res.country.state', string='State',
                               domain="[('country_id', '=', country_id)]",
                               help='The State in which port located')
    country_id = fields.Many2one('res.country', required=True,
                                 string='Country',
                                 help='The Country in which port located')
    active = fields.Boolean(string='Active', default=True,
                            help='For activate the Port')
    land = fields.Boolean(string='Land', help='Enable it if the medium is Land')
    air = fields.Boolean(string='Air', help='Enable it if the medium is Air')
    water = fields.Boolean(string='Water',
                           help='Enable it if the medium is Water')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
