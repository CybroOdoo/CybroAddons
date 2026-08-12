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


class FleetRentalAddon(models.Model):
    """Rental Add-on Option."""
    _name = 'fleet.rental.addon'
    _description = 'Rental Add-on Option'

    name = fields.Char(string='Add-on Name', required=True,
                       help='Name of the add-on.')
    description = fields.Text(string='Description',
                              help='Description of the add-on.')
    price = fields.Float(string='Price', required=True, default=0.0,
                         help='Cost of the add-on.')
    charge_type = fields.Selection(
        selection=[
            ('per_day', 'Per Day'),
            ('flat_fee', 'Flat Fee')
        ],
        string='Charge Type',
        default='flat_fee',
        required=True,
        help='How the add-on is charged.'
    )
    icon = fields.Char(string='Icon Class', help='e.g., fa-baby-carriage')
    active = fields.Boolean(string='Active', default=True,
                            help='Is the add-on active?')
