# -*- coding: utf-8 -*-
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


class FleetRentalInsurance(models.Model):
    """Rental Insurance Plan."""
    _name = 'fleet.rental.insurance'
    _description = 'Rental Insurance Plan'

    name = fields.Char(string='Plan Name', required=True,
                       help='Name of the insurance plan.')
    description = fields.Text(string='Description',
                              help='Description of the insurance coverage.')
    price_per_day = fields.Float(string='Price Per Day', required=True,
                                 default=0.0,
                                 help='Daily cost of the insurance.')
    is_default = fields.Boolean(string='Default Plan',
                                help='Is this the default plan?')
    active = fields.Boolean(string='Active', default=True,
                            help='Is the insurance plan active?')

