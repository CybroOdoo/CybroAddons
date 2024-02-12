# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
#############################################################################
"""This module enables users to place online orders and
pick up their purchases from nearby stores. """
from odoo import fields, models


class PosConfig(models.Model):
    """inherited for adding address in pos session"""
    _inherit = 'pos.config'

    street = fields.Char('Street', required=True,
                         help='Enter Address for your store')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', help='Enter zip for your store')
    city = fields.Char('City', required=True,
                       help='Enter your store located city')
    state_id = fields.Many2one("res.country.state", string='State',
                               required=True, help='Enter state')
    country_id = fields.Many2one('res.country', string='Country',
                                 required=True, help='Enter country')
