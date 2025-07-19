# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
"""This module enables users to place online orders and
pick up their purchases from nearby stores. """
from odoo import fields, models


class PosConfig(models.Model):
    """inherited for adding address in pos session"""
    _inherit = 'pos.config'

    street = fields.Char(string='Street', required=True,
                         help='Enter Address for your store')
    street2 = fields.Char(string='Street2', help="Street")
    zip = fields.Char(string='Zip', help='Enter zip for your store')
    city = fields.Char(string='City', required=True,
                       help='Enter your store located city')
    state_id = fields.Many2one("res.country.state", string='State',
                               required=True, help='Enter state')
    country_id = fields.Many2one('res.country', string='Country',
                                 required=True, help='Enter country')
