#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class FreightPort(models.Model):
    """Creating different port location for managing freight"""
    _name = 'freight.port'
    _description = 'Freight Port'

    name = fields.Char(help='Name for the port')
    code = fields.Char(help='Specify a code for freight')
    state_id = fields.Many2one(
        'res.country.state', domain="[('country_id', '=', country_id)]",
        help='The state in which port located')
    country_id = fields.Many2one('res.country', required=True,
                                 help='The country in which port located')
    active = fields.Boolean(default=True, help='To activate the port')
    land = fields.Boolean(help='Enable it if the medium is Land')
    air = fields.Boolean(help='Enable it if the medium is Air')
    water = fields.Boolean(help='Enable it if the medium is Water')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)
